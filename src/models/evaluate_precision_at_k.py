"""Phase 2 formal evaluation: precision@K / recall@K / lift@K for the
logistic regression and LightGBM baselines, against a random-targeting
baseline, reported on test exactly once (docs/decisions/004-three-way-split.md).

Both models are refit here rather than saved/reloaded from the earlier
sessions - LightGBM still uses val for early stopping (model selection, not
the reported number), same as when it was first built. Only test is newly
touched by this script's scoring/metrics.

K is expressed as a fraction of the test population (0.1%-5%) rather than a
fixed count, so the same script works regardless of the exact test-set size:
- precision@K: of the top-K contacted customers by predicted score, what
  fraction actually adopt.
- recall@K: of all adopters in the whole test set, what fraction fall inside
  that top-K contact list.
- lift@K: precision@K divided by the overall test adoption rate - how much
  better than random targeting the top-K list is.
Random targeting's expected precision@K is just the base rate (any random
sample estimates the population rate); its expected recall@K is k_frac
itself (a random k_frac-sized sample captures k_frac of the positives in
expectation).
"""

from pathlib import Path

import numpy as np
import pandas as pd

from models.baseline_lightgbm import fit_baseline as fit_lightgbm
from models.baseline_logistic_regression import (
    FEATURE_COLS,
    MODELING_TABLE_PATH,
    fit_baseline as fit_logistic_regression,
    prepare_features,
    scale_continuous,
)

K_FRACS = [0.001, 0.005, 0.01, 0.02, 0.05]


def load_all_splits() -> pd.DataFrame:
    return pd.read_parquet(MODELING_TABLE_PATH, columns=FEATURE_COLS + ["adoption", "split"])


def precision_recall_lift_at_k(y_true: pd.Series, scores: np.ndarray, k_frac: float) -> dict:
    n_contacted = max(1, int(len(y_true) * k_frac))
    top_idx = np.argsort(-scores)[:n_contacted]
    y_true_arr = y_true.to_numpy()
    n_adopters_captured = y_true_arr[top_idx].sum()
    base_rate = y_true_arr.mean()

    precision = n_adopters_captured / n_contacted
    recall = n_adopters_captured / y_true_arr.sum()
    lift = precision / base_rate

    return {
        "k_frac": k_frac,
        "n_contacted": n_contacted,
        "n_adopters_captured": int(n_adopters_captured),
        "precision": precision,
        "recall": recall,
        "lift": lift,
    }


def random_targeting_at_k(y_true: pd.Series, k_frac: float) -> dict:
    n_contacted = max(1, int(len(y_true) * k_frac))
    base_rate = y_true.mean()
    return {
        "k_frac": k_frac,
        "n_contacted": n_contacted,
        "n_adopters_captured": round(base_rate * n_contacted),
        "precision": base_rate,
        "recall": k_frac,
        "lift": 1.0,
    }


def build_comparison_table(y_test: pd.Series, model_scores: dict[str, np.ndarray]) -> pd.DataFrame:
    rows = []
    for k_frac in K_FRACS:
        for model_name, scores in model_scores.items():
            rows.append({"model": model_name, **precision_recall_lift_at_k(y_test, scores, k_frac)})
        rows.append({"model": "random", **random_targeting_at_k(y_test, k_frac)})
    return pd.DataFrame(rows)


def print_comparison_table(table: pd.DataFrame) -> None:
    display = table.copy()
    display["k_frac"] = display["k_frac"].map(lambda x: f"{x:.1%}")
    display["precision"] = display["precision"].map(lambda x: f"{x:.3%}")
    display["recall"] = display["recall"].map(lambda x: f"{x:.1%}")
    display["lift"] = display["lift"].map(lambda x: f"{x:.2f}x")
    print(display.to_string(index=False))


if __name__ == "__main__":
    df = load_all_splits()
    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "val"]
    test_df = df[df["split"] == "test"]

    X_train, y_train = prepare_features(train_df)
    X_val, y_val = prepare_features(val_df)
    X_test, y_test = prepare_features(test_df)

    print(f"test set: n={len(y_test):,}, adoption_rate={y_test.mean():.3%}\n")

    X_train_scaled, X_val_scaled, scaler = scale_continuous(X_train, X_val)
    X_test_scaled = X_test.copy()
    X_test_scaled[scaler.feature_names_in_] = scaler.transform(X_test[scaler.feature_names_in_])

    lr_model = fit_logistic_regression(X_train_scaled, y_train)
    lr_scores = lr_model.predict_proba(X_test_scaled)[:, 1]

    lgb_model = fit_lightgbm(X_train, y_train, X_val, y_val)
    lgb_scores = lgb_model.predict_proba(X_test)[:, 1]

    table = build_comparison_table(y_test, {"logistic_regression": lr_scores, "lightgbm": lgb_scores})
    print_comparison_table(table)

    out_path = Path(__file__).resolve().parents[2] / "reports" / "baseline_precision_at_k.csv"
    table.to_csv(out_path, index=False)
    print(f"\nWrote comparison table to {out_path}")

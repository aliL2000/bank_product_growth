"""Phase 3 diagnostic: is LightGBM's predicted probability trustworthy at the
top of the ranking, or does it overstate real observed rates for rare
feature combinations?

Prompted by /audit finding [uncalibrated-rare-leaf-scored-as-high-propensity]
(docs/audit_log.md, 2026-09-21): val's single highest-scored customer
(99.9997% predicted probability) sits in a feature-combination group
(`segmento_missing=True`, `product_count_prev=0`, `activity_index=0`) whose
*real* observed adoption rate turned out to be below val's overall average,
not above it - a below-average group producing a near-certain individual
prediction. Ranking metrics (ROC-AUC, precision@K) can't catch this, since
they only require adopters to sort above non-adopters on average - they
don't check whether "99.9997%" means what it says for any specific row or
group.

Calibration is measured here as mean_predicted_prob vs. observed_rate within
the top-K slice of val by score, at the same K fractions
`evaluate_precision_at_k.py` uses (plus a finer one near the very top, since
that's where the flagged customer sits) - not equal-width probability bins,
which would waste resolution on the ~99% of rows near zero and give none to
the tail Phase 3's segment work will actually draw candidates from.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from models.baseline_lightgbm import fit_baseline
from models.baseline_logistic_regression import load_train_val, prepare_features

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

K_FRACS = [0.0001, 0.001, 0.005, 0.01, 0.02, 0.05]

# The exact profile flagged in notebooks/08_shap_explainability.ipynb's
# single-customer walkthrough.
FLAGGED_PROFILE = {
    "segmento_missing": 1,
    "product_count_prev": 0,
    "activity_index": 0,
}


def calibration_at_k(y_true: pd.Series, scores: np.ndarray, k_frac: float) -> dict:
    """Mean predicted probability vs. observed adoption rate among the top
    k_frac of rows by score. calibration_ratio > 1 means the model is
    overconfident in that slice (predicted probabilities overstate the real
    rate); ~1 means the probabilities are trustworthy, not just the ranking."""
    n = max(1, int(len(y_true) * k_frac))
    top_idx = np.argsort(-scores)[:n]
    y_arr = y_true.to_numpy()

    observed_rate = y_arr[top_idx].mean()
    mean_predicted = scores[top_idx].mean()

    return {
        "k_frac": k_frac,
        "n": n,
        "mean_predicted_prob": mean_predicted,
        "observed_rate": observed_rate,
        "calibration_ratio": mean_predicted / observed_rate if observed_rate > 0 else np.nan,
    }


def calibration_table(y_true: pd.Series, scores: np.ndarray, k_fracs: list[float] = K_FRACS) -> pd.DataFrame:
    return pd.DataFrame([calibration_at_k(y_true, scores, k) for k in k_fracs])


def group_observed_vs_predicted(df: pd.DataFrame, scores: np.ndarray, profile: dict) -> dict:
    """Same observed-rate-vs-predicted-probability comparison, but for an
    explicit feature-combination group (a fixed profile) instead of a top-K
    slice by score - directly reproduces the audit's by-hand check on the
    flagged customer's group as a permanent, reusable diagnostic."""
    mask = np.ones(len(df), dtype=bool)
    for col, val in profile.items():
        mask &= (df[col] == val).to_numpy()

    y_arr = df["adoption"].to_numpy()
    return {
        "n": int(mask.sum()),
        "observed_rate": y_arr[mask].mean(),
        "mean_predicted_prob": scores[mask].mean(),
        "max_predicted_prob": scores[mask].max(),
    }


def print_calibration_table(table: pd.DataFrame) -> None:
    display = table.copy()
    display["k_frac"] = display["k_frac"].map(lambda x: f"{x:.2%}")
    display["mean_predicted_prob"] = display["mean_predicted_prob"].map(lambda x: f"{x:.3%}")
    display["observed_rate"] = display["observed_rate"].map(lambda x: f"{x:.3%}")
    display["calibration_ratio"] = display["calibration_ratio"].map(lambda x: f"{x:.2f}x")
    print("\ncalibration by top-K slice (mean predicted prob vs. observed rate):")
    print(display.to_string(index=False))


if __name__ == "__main__":
    df = load_train_val()
    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "val"]

    X_train, y_train = prepare_features(train_df)
    X_val, y_val = prepare_features(val_df)

    model = fit_baseline(X_train, y_train, X_val, y_val)
    scores = model.predict_proba(X_val)[:, 1]

    table = calibration_table(y_val, scores)
    print_calibration_table(table)

    flagged = group_observed_vs_predicted(val_df, scores, FLAGGED_PROFILE)
    print(f"\nflagged group ({FLAGGED_PROFILE}):")
    print(f"  n={flagged['n']:,}, observed_rate={flagged['observed_rate']:.3%}, "
          f"mean_predicted_prob={flagged['mean_predicted_prob']:.3%}, "
          f"max_predicted_prob={flagged['max_predicted_prob']:.3%}")
    print(f"  overall val observed rate: {y_val.mean():.3%}")

    out_path = REPORTS_DIR / "calibration_check.csv"
    table.to_csv(out_path, index=False)
    print(f"\nWrote calibration table to {out_path}")

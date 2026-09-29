"""Phase 4 step 2: simulated profit of three targeting strategies on test.

Strategies (all priced with src/models/roi_assumptions.py's base case,
docs/decisions/005-simulated-roi-assumptions.md):
- model_top_k: contact the top-K customers by LightGBM score.
- segment_rule: contact every customer in the Phase 3 segment (active,
  particulares, exactly 1 existing product, aged 35-64) - a fixed list,
  whatever its size (reports/03_explainability_segments.md).
- contact_everyone: contact the whole population.

Choosing K: the profit-maximizing contact budget is picked on **val**, then
frozen and reported on test. Picking the peak of test's own profit curve
and reporting test's profit at that peak would be tuning on test - an
optimistic number (docs/decisions/004-three-way-split.md). Test's own
peak is printed alongside for context only, labelled as such.

The model is also scored at exactly the segment rule's list size, so the
model-vs-rule comparison isn't confounded by the two lists having
different sizes.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from models.baseline_lightgbm import fit_baseline as fit_lightgbm
from models.baseline_logistic_regression import FEATURE_COLS, MODELING_TABLE_PATH, prepare_features
from models.identify_segments import build_group_columns
from models.roi_assumptions import break_even_precision, simulated_profit

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

# Finer than Phase 2's K_FRACS so the profit curve's peak is actually located,
# not just bracketed.
BUDGET_FRACS = [0.0005, 0.001, 0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02, 0.03, 0.05, 0.075, 0.10]

SEGMENT_AGE_BANDS = ["35-44", "45-54", "55-64"]


def in_segment(df: pd.DataFrame) -> pd.Series:
    """The Phase 3 segment as a boolean mask, built with the same grouping
    helpers identify_segments.py used, so the rule can't drift from it."""
    groups = build_group_columns(df)
    return (
        (groups["product_tier"] == "1")
        & (groups["segmento_label"] == "particulares")
        & (groups["activity_label"] == "active")
        & groups["age_band"].isin(SEGMENT_AGE_BANDS)
    )


def list_result(strategy: str, y_true: np.ndarray, contacted: np.ndarray) -> dict:
    """Size, adopters captured, precision and simulated profit of one contact list."""
    n_contacted = int(contacted.sum())
    adopters = int(y_true[contacted].sum())
    return {
        "strategy": strategy,
        "n_contacted": n_contacted,
        "budget_frac": n_contacted / len(y_true),
        "adopters_captured": adopters,
        "precision": adopters / n_contacted if n_contacted else 0.0,
        "profit_eur": simulated_profit(n_contacted, adopters),
    }


def top_k_mask(scores: np.ndarray, n_contacted: int) -> np.ndarray:
    mask = np.zeros(len(scores), dtype=bool)
    mask[np.argsort(-scores)[:n_contacted]] = True
    return mask


def profit_curve(y_true: np.ndarray, scores: np.ndarray, budget_fracs=BUDGET_FRACS) -> pd.DataFrame:
    rows = []
    for frac in budget_fracs:
        n = max(1, int(len(y_true) * frac))
        rows.append(list_result("model_top_k", y_true, top_k_mask(scores, n)))
    return pd.DataFrame(rows)


def best_budget_frac(curve: pd.DataFrame) -> float:
    return float(curve.loc[curve["profit_eur"].idxmax(), "budget_frac"])


def compare_strategies(y_true: np.ndarray, scores: np.ndarray, segment_mask: np.ndarray,
                       chosen_budget_frac: float) -> pd.DataFrame:
    n_chosen = max(1, int(len(y_true) * chosen_budget_frac))
    rows = [
        list_result("model_top_k @ val-chosen budget", y_true, top_k_mask(scores, n_chosen)),
        list_result("segment_rule", y_true, segment_mask),
        list_result("model_top_k @ segment's list size", y_true, top_k_mask(scores, int(segment_mask.sum()))),
        list_result("contact_everyone", y_true, np.ones(len(y_true), dtype=bool)),
    ]
    return pd.DataFrame(rows)


def format_table(table: pd.DataFrame) -> str:
    display = table.copy()
    display["budget_frac"] = display["budget_frac"].map(lambda x: f"{x:.2%}")
    display["precision"] = display["precision"].map(lambda x: f"{x:.3%}")
    display["profit_eur"] = display["profit_eur"].map(lambda x: f"{x:,.0f}")
    return display.to_string(index=False)


if __name__ == "__main__":
    # FEATURE_COLS already holds every raw column in_segment() needs.
    df = pd.read_parquet(MODELING_TABLE_PATH, columns=FEATURE_COLS + ["adoption", "split"])
    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "val"]
    test_df = df[df["split"] == "test"]

    X_train, y_train = prepare_features(train_df)
    X_val, y_val = prepare_features(val_df)
    X_test, y_test = prepare_features(test_df)

    model = fit_lightgbm(X_train, y_train, X_val, y_val)
    val_scores = model.predict_proba(X_val)[:, 1]
    test_scores = model.predict_proba(X_test)[:, 1]
    y_val_arr, y_test_arr = y_val.to_numpy(), y_test.to_numpy()

    print(f"break-even precision (base case): {break_even_precision():.3%}\n")

    val_curve = profit_curve(y_val_arr, val_scores)
    chosen = best_budget_frac(val_curve)
    print("val profit curve (used to choose the budget):")
    print(format_table(val_curve))
    print(f"\n-> budget chosen on val: {chosen:.2%} of customers\n")

    test_curve = profit_curve(y_test_arr, test_scores)
    print("test profit curve (context only - its peak is NOT the reported number):")
    print(format_table(test_curve))
    print(f"\n(test's own peak would have been {best_budget_frac(test_curve):.2%})\n")

    segment_mask = in_segment(test_df).to_numpy()
    comparison = compare_strategies(y_test_arr, test_scores, segment_mask, chosen)
    print("strategy comparison on test:")
    print(format_table(comparison))

    val_curve.assign(split="val").pipe(
        lambda v: pd.concat([v, test_curve.assign(split="test")])
    ).to_csv(REPORTS_DIR / "targeting_profit_curve.csv", index=False)
    comparison.to_csv(REPORTS_DIR / "targeting_strategy_comparison.csv", index=False)
    print(f"\nWrote {REPORTS_DIR / 'targeting_profit_curve.csv'}")
    print(f"Wrote {REPORTS_DIR / 'targeting_strategy_comparison.csv'}")

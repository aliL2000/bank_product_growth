"""Phase 4 steps 2-3: simulated profit of three targeting strategies on test,
under the base case and across the full sensitivity sweep.

Strategies (priced with src/models/roi_assumptions.py,
docs/decisions/005-simulated-roi-assumptions.md):
- model_top_k: contact the top-K customers by LightGBM score.
- segment_rule: contact every customer in the Phase 3 segment (active,
  particulares, exactly 1 existing product, aged 35-64) - a fixed list,
  whatever its size (reports/03_explainability_segments.md).
- contact_everyone: contact the whole population.

Choosing K: the profit-maximizing contact budget is picked on **val**, then
frozen and reported on test. Picking the peak of test's own profit curve
and reporting test's profit at that peak would be tuning on test - an
optimistic number (docs/decisions/004-three-way-split.md). The peak is found
on the exact profit curve (every K from 0 to n), not a coarse budget grid,
because in low-break-even scenarios it can sit far beyond any grid point.

The model is also scored at exactly the segment rule's list size, so the
model-vs-rule comparison isn't confounded by the two lists having
different sizes.

Sweep: every cost x value x uplift combination from roi_assumptions.py (full
grid, not one-at-a-time, so interactions show up). Profit =
u*V*(adopters - K*c/(u*V)), so the best list depends only on the break-even
precision c/(u*V); u*V only scales the profit.
"""

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from models.baseline_lightgbm import fit_baseline as fit_lightgbm
from models.baseline_logistic_regression import FEATURE_COLS, MODELING_TABLE_PATH, prepare_features
from models.identify_segments import build_group_columns
from models.roi_assumptions import (
    COST_PER_CONTACT,
    COST_SWEEP,
    UPLIFT,
    UPLIFT_SWEEP,
    VALUE_PER_ADOPTION,
    VALUE_SWEEP,
    break_even_precision,
    simulated_profit,
)

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

# Display grid only - the chosen budget comes from the exact curve.
BUDGET_FRACS = [0.0005, 0.001, 0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02, 0.03, 0.05, 0.075, 0.10]

SEGMENT_AGE_BANDS = ["35-44", "45-54", "55-64"]

# Smallest list that counts as a campaign. Without a floor, the exact argmax
# in scenarios where no real campaign pays lands on 2-3 customers that
# happened to include an adopter (50% "precision") - noise, not a budget.
# At the model's ~9% top precision, 1,000 contacts ~ 90 expected adopters:
# enough that precision reflects the ranking, not a few lucky rows. Equals
# the smallest display budget (0.05% of ~1.75M val rows ~ 875-1,332).
MIN_CAMPAIGN_SIZE = 1000

BASE_ECON = {"cost_per_contact": COST_PER_CONTACT, "value_per_adoption": VALUE_PER_ADOPTION, "uplift": UPLIFT}


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


def list_result(strategy: str, y_true: np.ndarray, contacted: np.ndarray, **econ) -> dict:
    """Size, adopters captured, precision and simulated profit of one contact list."""
    n_contacted = int(contacted.sum())
    adopters = int(y_true[contacted].sum())
    return {
        "strategy": strategy,
        "n_contacted": n_contacted,
        "budget_frac": n_contacted / len(y_true),
        "adopters_captured": adopters,
        "precision": adopters / n_contacted if n_contacted else 0.0,
        "profit_eur": simulated_profit(n_contacted, adopters, **econ),
    }


def top_k_mask(scores: np.ndarray, n_contacted: int) -> np.ndarray:
    mask = np.zeros(len(scores), dtype=bool)
    mask[np.argsort(-scores, kind="stable")[:n_contacted]] = True
    return mask


def exact_profit_curve(y_true: np.ndarray, scores: np.ndarray, **econ) -> np.ndarray:
    """Profit of contacting the top-K by score, for every K = 0..n (index = K)."""
    cum_adopters = np.concatenate([[0], np.cumsum(y_true[np.argsort(-scores, kind="stable")])])
    return simulated_profit(np.arange(len(y_true) + 1), cum_adopters, **econ)


def best_budget_frac(y_true: np.ndarray, scores: np.ndarray,
                     min_campaign_size: int = MIN_CAMPAIGN_SIZE, **econ) -> float:
    """Profit-maximizing share of the population to contact, considering only
    K = 0 (no campaign) or K >= min_campaign_size. Returns 0 when no
    campaign of at least that size makes a profit."""
    curve = exact_profit_curve(y_true, scores, **econ)
    floor = min(min_campaign_size, len(y_true))
    best_k = floor + int(np.argmax(curve[floor:]))
    return best_k / len(y_true) if curve[best_k] > 0 else 0.0


def profit_curve(y_true: np.ndarray, scores: np.ndarray, budget_fracs=BUDGET_FRACS, **econ) -> pd.DataFrame:
    rows = []
    for frac in budget_fracs:
        n = max(1, int(len(y_true) * frac))
        rows.append(list_result("model_top_k", y_true, top_k_mask(scores, n), **econ))
    return pd.DataFrame(rows)


def compare_strategies(y_true: np.ndarray, scores: np.ndarray, segment_mask: np.ndarray,
                       chosen_budget_frac: float, **econ) -> pd.DataFrame:
    n_chosen = int(round(len(y_true) * chosen_budget_frac))
    rows = [
        list_result("model_top_k @ val-chosen budget", y_true, top_k_mask(scores, n_chosen), **econ),
        list_result("segment_rule", y_true, segment_mask, **econ),
        list_result("model_top_k @ segment's list size", y_true,
                    top_k_mask(scores, int(segment_mask.sum())), **econ),
        list_result("contact_everyone", y_true, np.ones(len(y_true), dtype=bool), **econ),
    ]
    return pd.DataFrame(rows)


def sensitivity_sweep(y_val: np.ndarray, val_scores: np.ndarray, y_test: np.ndarray,
                      test_scores: np.ndarray, segment_mask: np.ndarray) -> pd.DataFrame:
    """One row per cost x value x uplift scenario: budget chosen on val, then
    each strategy's test profit at that scenario's economics."""
    rows = []
    for (channel, cost), value, uplift in product(COST_SWEEP.items(), VALUE_SWEEP, UPLIFT_SWEEP):
        econ = {"cost_per_contact": cost, "value_per_adoption": value, "uplift": uplift}
        chosen = best_budget_frac(y_val, val_scores, **econ)
        table = compare_strategies(y_test, test_scores, segment_mask, chosen, **econ).set_index("strategy")
        rows.append({
            "channel": channel,
            "cost_per_contact": cost,
            "value_per_adoption": value,
            "uplift": uplift,
            "break_even_precision": break_even_precision(**econ),
            "val_chosen_budget_frac": chosen,
            "model_precision": table.loc["model_top_k @ val-chosen budget", "precision"],
            "model_profit_eur": table.loc["model_top_k @ val-chosen budget", "profit_eur"],
            "segment_rule_profit_eur": table.loc["segment_rule", "profit_eur"],
            "contact_everyone_profit_eur": table.loc["contact_everyone", "profit_eur"],
        })
    return pd.DataFrame(rows)


def format_table(table: pd.DataFrame) -> str:
    display = table.copy()
    for col in display.columns:
        if col in ("budget_frac", "val_chosen_budget_frac", "precision", "model_precision",
                   "break_even_precision", "uplift"):
            display[col] = display[col].map(lambda x: f"{x:.2%}")
        elif col.endswith("profit_eur"):
            display[col] = display[col].map(lambda x: f"{x:,.0f}")
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
    segment_mask = in_segment(test_df).to_numpy()

    # --- Step 2: base case ---
    print(f"break-even precision (base case): {break_even_precision():.3%}\n")
    val_curve = profit_curve(y_val_arr, val_scores)
    test_curve = profit_curve(y_test_arr, test_scores)
    print("val profit curve (display grid):")
    print(format_table(val_curve))
    print("\ntest profit curve (display grid, context only):")
    print(format_table(test_curve))

    chosen = best_budget_frac(y_val_arr, val_scores)
    print(f"\n-> budget chosen on val (exact curve): {chosen:.2%} of customers")
    print(f"   (test's own exact peak would have been {best_budget_frac(y_test_arr, test_scores):.2%} "
          "- context only, not used)\n")

    comparison = compare_strategies(y_test_arr, test_scores, segment_mask, chosen)
    print("base-case strategy comparison on test:")
    print(format_table(comparison))

    # --- Step 3: sensitivity sweep ---
    sweep = sensitivity_sweep(y_val_arr, val_scores, y_test_arr, test_scores, segment_mask)
    print("\nsensitivity sweep (test profit, budget chosen on val per scenario):")
    print(format_table(sweep))

    pd.concat([val_curve.assign(split="val"), test_curve.assign(split="test")]).to_csv(
        REPORTS_DIR / "targeting_profit_curve.csv", index=False)
    comparison.to_csv(REPORTS_DIR / "targeting_strategy_comparison.csv", index=False)
    sweep.to_csv(REPORTS_DIR / "targeting_sensitivity_sweep.csv", index=False)
    print(f"\nWrote targeting_profit_curve.csv, targeting_strategy_comparison.csv, "
          f"targeting_sensitivity_sweep.csv to {REPORTS_DIR}")

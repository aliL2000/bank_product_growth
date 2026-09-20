"""Phase 3 explainability: SHAP values on the LightGBM baseline.

Runs SHAP on LightGBM, not logistic regression - LR's 18 coefficients are
already a complete, exact explanation of it (for a linear model, a SHAP
value literally reduces to coefficient * (feature - mean)), so running SHAP
on LR would just re-derive numbers already printed by
`baseline_logistic_regression.print_coefficients`. LightGBM is the model
that's actually opaque (36 trees, no single global coefficient), which is
what SHAP is for.

Computed on val, not test - SHAP isn't a "reported metric" the way
precision@K is (docs/decisions/004-three-way-split.md), but there's no
reason to spend test's one-time-only guarantee on an exploratory step, so
it stays untouched.

Uses `shap.TreeExplainer`'s default 'raw' model_output: SHAP values are on
the model's raw margin (log-odds) scale, not probability - they sum exactly
to (this prediction's raw score - expected_value) on that scale. Converting
to probability would break the clean additivity property (sigmoid isn't
linear), so ranking/direction is read in log-odds space; only relative
magnitude and sign are used for the narrative, not "N percentage points."
"""

from pathlib import Path

import numpy as np
import pandas as pd
import shap

from models.baseline_lightgbm import fit_baseline
from models.baseline_logistic_regression import FEATURE_COLS, load_train_val, prepare_features

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"


def compute_shap_values(model, X: pd.DataFrame) -> tuple[np.ndarray, float]:
    """Exact Shapley values for a tree ensemble via TreeExplainer.
    `check_additivity=True` (the default) verifies shap_values.sum(axis=1) +
    expected_value reproduces the model's raw score for every row - a
    correctness check, not just a nice-to-have."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X, check_additivity=True)
    return shap_values, explainer.expected_value


def global_importance(shap_values: np.ndarray, feature_cols: list[str]) -> pd.Series:
    """Mean |SHAP value| per feature - the SHAP analog of LightGBM's
    split-count importance, but weighted by actual impact on predictions
    rather than how often a feature was touched."""
    mean_abs = np.abs(shap_values).mean(axis=0)
    return pd.Series(mean_abs, index=feature_cols).sort_values(ascending=False)


def feature_direction(X: pd.DataFrame, shap_values: np.ndarray, feature_cols: list[str]) -> pd.Series:
    """Correlation between each feature's raw value and its own SHAP value -
    a compact stand-in for 'which way does this feature push predictions,
    on average' (what a beeswarm plot shows visually), used to cross-check
    against logistic regression's coefficient signs.

    A handful of the `*_missing` flags are near-constant in val (e.g.
    `activity_missing`/`product_count_missing` are False for every val row -
    train's ~0.16% missing rate barely shows up in val's 2-month window),
    and a feature the model never split on has an all-zero SHAP column
    (e.g. `tenure_missing`/`sexo_missing` above). Either makes correlation
    undefined; returned as NaN rather than letting numpy warn about a
    divide-by-zero on a degenerate column."""
    corrs = {}
    for i, col in enumerate(feature_cols):
        if X[col].std() == 0 or shap_values[:, i].std() == 0:
            corrs[col] = np.nan
        else:
            corrs[col] = np.corrcoef(X[col], shap_values[:, i])[0, 1]
    return pd.Series(corrs).reindex(feature_cols)


def print_shap_summary(importance: pd.Series, direction: pd.Series) -> None:
    summary = pd.DataFrame({"mean_abs_shap": importance, "direction_corr": direction.reindex(importance.index)})
    print("\nSHAP global importance (mean |SHAP value|, log-odds scale) + direction:")
    print(summary.to_string())


if __name__ == "__main__":
    df = load_train_val()
    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "val"]

    X_train, y_train = prepare_features(train_df)
    X_val, y_val = prepare_features(val_df)

    model = fit_baseline(X_train, y_train, X_val, y_val)
    print(f"fit LightGBM: best_iteration_={model.best_iteration_}, val n={len(y_val):,}")

    shap_values, expected_value = compute_shap_values(model, X_val)
    print(f"expected_value (log-odds baseline): {expected_value:.4f}")

    importance = global_importance(shap_values, FEATURE_COLS)
    direction = feature_direction(X_val, shap_values, FEATURE_COLS)
    print_shap_summary(importance, direction)

    out_path = REPORTS_DIR / "shap_global_importance.csv"
    pd.DataFrame({"mean_abs_shap": importance, "direction_corr": direction.reindex(importance.index)}).to_csv(out_path)
    print(f"\nWrote global importance table to {out_path}")

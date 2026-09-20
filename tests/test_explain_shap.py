"""Unit tests for explain_shap.py, on small synthetic data."""

import numpy as np
import pandas as pd

from models.baseline_logistic_regression import BINARY_COLS, CONTINUOUS_COLS
from models.baseline_lightgbm import fit_baseline
from models.explain_shap import compute_shap_values, feature_direction, global_importance

FEATURE_COLS = CONTINUOUS_COLS + BINARY_COLS


def _synthetic_split(n, seed):
    rng = np.random.default_rng(seed)
    data = {col: rng.normal(size=n) for col in CONTINUOUS_COLS}
    data.update({col: rng.integers(0, 2, size=n) for col in BINARY_COLS})
    X = pd.DataFrame(data)
    # target correlated with the first continuous column, so there's a
    # learnable, directionally-predictable signal to check SHAP against.
    y = pd.Series((X[CONTINUOUS_COLS[0]] + rng.normal(scale=0.5, size=n) > 0).astype("int8"))
    return X, y


def test_shap_values_sum_to_raw_score_minus_expected_value():
    # the core SHAP guarantee: per row, shap_values.sum() + expected_value
    # reproduces the model's raw (log-odds) score exactly.
    X_train, y_train = _synthetic_split(200, seed=1)
    X_val, y_val = _synthetic_split(50, seed=2)
    model = fit_baseline(X_train, y_train, X_val, y_val)

    shap_values, expected_value = compute_shap_values(model, X_val)
    raw_scores = model.predict(X_val, raw_score=True)

    reconstructed = shap_values.sum(axis=1) + expected_value
    np.testing.assert_allclose(reconstructed, raw_scores, atol=1e-6)


def test_global_importance_ranks_the_informative_feature_highest():
    X_train, y_train = _synthetic_split(300, seed=1)
    X_val, y_val = _synthetic_split(80, seed=2)
    model = fit_baseline(X_train, y_train, X_val, y_val)

    shap_values, _ = compute_shap_values(model, X_val)
    importance = global_importance(shap_values, FEATURE_COLS)

    # CONTINUOUS_COLS[0] is the only feature the synthetic label depends on.
    assert importance.index[0] == CONTINUOUS_COLS[0]


def test_feature_direction_is_nan_for_a_constant_column():
    X_train, y_train = _synthetic_split(300, seed=1)
    X_val, y_val = _synthetic_split(80, seed=2)
    X_val = X_val.copy()
    X_val[BINARY_COLS[0]] = 0  # make one column constant, like val's near-zero missing flags

    model = fit_baseline(X_train, y_train, X_val, y_val)
    shap_values, _ = compute_shap_values(model, X_val)
    direction = feature_direction(X_val, shap_values, FEATURE_COLS)

    assert np.isnan(direction[BINARY_COLS[0]])
    assert not direction.drop(BINARY_COLS[0]).isna().all()

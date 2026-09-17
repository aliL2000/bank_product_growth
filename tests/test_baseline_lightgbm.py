"""Unit tests for baseline_lightgbm.py's own logic (fit_baseline, since the
data-loading/feature-selection/lift helpers are already covered by
test_baseline_logistic_regression.py), on small synthetic data."""

import numpy as np
import pandas as pd

from models.baseline_logistic_regression import BINARY_COLS, CONTINUOUS_COLS
from models.baseline_lightgbm import fit_baseline


def _synthetic_split(n, seed):
    rng = np.random.default_rng(seed)
    data = {col: rng.normal(size=n) for col in CONTINUOUS_COLS}
    data.update({col: rng.integers(0, 2, size=n) for col in BINARY_COLS})
    X = pd.DataFrame(data)
    # target correlated with the first continuous column, so there's a
    # learnable signal for the model to actually split on.
    y = pd.Series((X[CONTINUOUS_COLS[0]] + rng.normal(scale=0.5, size=n) > 0).astype("int8"))
    return X, y


def test_fit_baseline_trains_and_produces_valid_probabilities():
    X_train, y_train = _synthetic_split(200, seed=1)
    X_val, y_val = _synthetic_split(50, seed=2)

    model = fit_baseline(X_train, y_train, X_val, y_val)
    scores = model.predict_proba(X_val)[:, 1]

    assert ((scores >= 0) & (scores <= 1)).all()


def test_fit_baseline_uses_early_stopping_not_the_full_budget():
    X_train, y_train = _synthetic_split(200, seed=1)
    X_val, y_val = _synthetic_split(50, seed=2)

    model = fit_baseline(X_train, y_train, X_val, y_val)

    # n_estimators=500 inside fit_baseline; early stopping should pick a
    # smaller number of rounds rather than exhausting the full budget.
    assert 0 < model.best_iteration_ < 500

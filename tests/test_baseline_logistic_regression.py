"""Unit tests for baseline_logistic_regression.py's pure helper functions,
on small synthetic data rather than the real 12M-row table."""

import pandas as pd

from models.baseline_logistic_regression import (
    BINARY_COLS,
    CONTINUOUS_COLS,
    prepare_features,
    scale_continuous,
    top_k_lift,
)


def _synthetic_df(split):
    n = len(split)
    data = {col: [float(i) for i in range(n)] for col in CONTINUOUS_COLS}
    data.update({col: [0] * n for col in BINARY_COLS})
    data["adoption"] = pd.array([i % 2 == 0 for i in range(n)], dtype="boolean")
    data["split"] = split
    return pd.DataFrame(data)


def test_prepare_features_selects_feature_cols_and_casts_target_to_int():
    df = _synthetic_df(["train", "train"])

    X, y = prepare_features(df)

    assert list(X.columns) == CONTINUOUS_COLS + BINARY_COLS
    assert y.dtype == "int8"
    assert y.tolist() == [1, 0]


def test_scale_continuous_fits_only_on_train_stats():
    train_df = _synthetic_df(["train"] * 4)
    train_df[CONTINUOUS_COLS] = [[0.0] * len(CONTINUOUS_COLS), [10.0] * len(CONTINUOUS_COLS),
                                  [0.0] * len(CONTINUOUS_COLS), [10.0] * len(CONTINUOUS_COLS)]
    val_df = _synthetic_df(["val"] * 2)
    val_df[CONTINUOUS_COLS] = [[5.0] * len(CONTINUOUS_COLS), [5.0] * len(CONTINUOUS_COLS)]

    X_train, y_train = prepare_features(train_df)
    X_val, y_val = prepare_features(val_df)
    X_train_scaled, X_val_scaled, scaler = scale_continuous(X_train, X_val)

    # train mean is 5.0, train std is 5.0 -> a val value of 5.0 should scale to ~0
    assert abs(X_val_scaled[CONTINUOUS_COLS[0]].iloc[0]) < 1e-9
    assert scaler.mean_[0] == 5.0


def test_top_k_lift_is_above_one_when_scores_rank_adopters_first():
    y_true = pd.Series([1, 0, 0, 0, 1, 0, 0, 0, 0, 0])
    scores = [0.9, 0.1, 0.1, 0.1, 0.9, 0.1, 0.1, 0.1, 0.1, 0.1]

    lift = top_k_lift(y_true, scores, k_frac=0.2)

    assert lift > 1.0

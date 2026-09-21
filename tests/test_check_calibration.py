"""Unit tests for check_calibration.py's metric helpers, on small synthetic
data with hand-computable expected values."""

import numpy as np
import pandas as pd
import pytest

from models.check_calibration import calibration_at_k, calibration_table, group_observed_vs_predicted


def test_calibration_at_k_is_1x_when_predicted_prob_matches_observed_rate():
    # top-20% (k_frac=0.2, n=2) is rows 0-1: both adopters, both scored 0.9 -
    # predicted (0.9) doesn't match observed (1.0) exactly, but consider a
    # case built to match exactly instead.
    y_true = pd.Series([1, 0, 1, 0, 0, 0, 0, 0, 0, 0])  # base rate 0.2
    scores = np.array([0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2])

    # every row scored at exactly the true base rate -> any slice's mean
    # predicted prob (0.2) should equal the overall observed rate (0.2).
    result = calibration_at_k(y_true, scores, k_frac=1.0)

    assert result["mean_predicted_prob"] == pytest.approx(0.2)
    assert result["observed_rate"] == pytest.approx(0.2)
    assert result["calibration_ratio"] == pytest.approx(1.0)


def test_calibration_at_k_flags_overconfidence_in_the_top_slice():
    # top-20% (n=2) are both non-adopters despite being scored at 0.99 -
    # observed rate in that slice is 0, so calibration_ratio should be NaN
    # (can't divide by zero), but mean_predicted_prob should still show the
    # inflated score plainly.
    y_true = pd.Series([0, 0, 1, 1, 0, 0, 0, 0, 0, 0])
    scores = np.array([0.99, 0.99, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05])

    result = calibration_at_k(y_true, scores, k_frac=0.2)

    assert result["n"] == 2
    assert result["observed_rate"] == 0.0
    assert result["mean_predicted_prob"] == pytest.approx(0.99)
    assert np.isnan(result["calibration_ratio"])


def test_calibration_at_k_detects_a_real_overconfident_slice():
    # top-30% (n=3): scores 0.9/0.9/0.9 but only 1 of the 3 is a real
    # adopter, so observed_rate=1/3 while mean_predicted_prob=0.9 ->
    # calibration_ratio should be clearly > 1 (overconfident).
    y_true = pd.Series([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    scores = np.array([0.9, 0.9, 0.9, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05])

    result = calibration_at_k(y_true, scores, k_frac=0.3)

    assert result["n"] == 3
    assert result["observed_rate"] == pytest.approx(1 / 3)
    assert result["mean_predicted_prob"] == pytest.approx(0.9)
    assert result["calibration_ratio"] > 2.0


def test_calibration_table_has_one_row_per_k_frac():
    y_true = pd.Series([1, 0] * 50)
    scores = np.linspace(1, 0, 100)

    table = calibration_table(y_true, scores, k_fracs=[0.1, 0.5])

    assert list(table["k_frac"]) == [0.1, 0.5]
    assert len(table) == 2


def test_group_observed_vs_predicted_filters_to_the_matching_profile():
    df = pd.DataFrame({
        "adoption": [1, 0, 0, 0],
        "segmento_missing": [1, 1, 0, 1],
        "product_count_prev": [0, 0, 0, 1],
        "activity_index": [0, 0, 0, 0],
    })
    scores = np.array([0.99, 0.5, 0.1, 0.8])
    profile = {"segmento_missing": 1, "product_count_prev": 0, "activity_index": 0}

    # rows 0 and 1 match the profile (row 2 fails segmento_missing, row 3
    # fails product_count_prev); observed rate among them is 0.5, mean
    # predicted prob is (0.99 + 0.5) / 2.
    result = group_observed_vs_predicted(df, scores, profile)

    assert result["n"] == 2
    assert result["observed_rate"] == pytest.approx(0.5)
    assert result["mean_predicted_prob"] == pytest.approx(0.745)
    assert result["max_predicted_prob"] == pytest.approx(0.99)

"""Unit tests for evaluate_precision_at_k.py's metric helpers, on small
synthetic data with hand-computable expected values."""

import numpy as np
import pandas as pd
import pytest

from models.evaluate_precision_at_k import (
    build_comparison_table,
    precision_recall_lift_at_k,
    random_targeting_at_k,
)


def test_precision_recall_lift_at_k_ranks_by_score_correctly():
    # 10 rows, adopters at indices 0 and 1, scores rank them at the very
    # top - so the top-20% (k_frac=0.2, n_contacted=2) should be a perfect
    # precision@K of 100% and capture both adopters (recall@K=100%).
    y_true = pd.Series([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    scores = np.array([0.9, 0.8, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])

    result = precision_recall_lift_at_k(y_true, scores, k_frac=0.2)

    assert result["n_contacted"] == 2
    assert result["n_adopters_captured"] == 2
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["lift"] == pytest.approx(5.0)


def test_precision_recall_lift_at_k_with_a_miss_in_top_k():
    # Same population, but the highest-scored row is a non-adopter - so the
    # top-20% only captures 1 of the 2 adopters.
    y_true = pd.Series([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    scores = np.array([0.1, 0.8, 0.9, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])

    result = precision_recall_lift_at_k(y_true, scores, k_frac=0.2)

    assert result["n_contacted"] == 2
    assert result["n_adopters_captured"] == 1
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5


def test_random_targeting_at_k_expects_the_base_rate_and_a_1x_lift():
    y_true = pd.Series([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])  # base rate 0.2

    result = random_targeting_at_k(y_true, k_frac=0.3)

    assert result["n_contacted"] == 3
    assert result["precision"] == 0.2
    assert result["recall"] == 0.3
    assert result["lift"] == 1.0


def test_build_comparison_table_includes_every_model_and_k_frac():
    y_true = pd.Series([1, 0] * 50)
    scores = {"model_a": np.linspace(0, 1, 100), "model_b": np.linspace(1, 0, 100)}

    table = build_comparison_table(y_true, scores)

    assert set(table["model"].unique()) == {"model_a", "model_b", "random"}
    assert len(table) == 5 * 3  # len(K_FRACS) * 3 models (2 real + random)

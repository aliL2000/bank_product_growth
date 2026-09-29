"""Unit tests for targeting_roi.py's strategy helpers, on small synthetic data
with hand-computable expected values (base-case assumptions: EUR 0.50/contact,
EUR 150/adoption, 20% uplift -> each captured adopter is worth EUR 30)."""

import numpy as np
import pandas as pd
import pytest

from models.targeting_roi import (
    best_budget_frac,
    compare_strategies,
    exact_profit_curve,
    in_segment,
    list_result,
    profit_curve,
    sensitivity_sweep,
    top_k_mask,
)


def test_list_result_profit_hand_computed():
    # 4 contacted, 1 adopter: 0.2 * 1 * 150 - 4 * 0.5 = 30 - 2 = 28.
    y = np.array([1, 0, 0, 0, 0, 0])
    contacted = np.array([True, True, True, True, False, False])
    result = list_result("x", y, contacted)
    assert result["n_contacted"] == 4
    assert result["adopters_captured"] == 1
    assert result["precision"] == pytest.approx(0.25)
    assert result["profit_eur"] == pytest.approx(28.0)


def test_top_k_mask_picks_highest_scores():
    scores = np.array([0.1, 0.9, 0.5, 0.7])
    assert top_k_mask(scores, 2).tolist() == [False, True, False, True]


def test_profit_curve_peaks_where_marginal_contacts_stop_paying():
    # 1,000 rows. Top 10 by score are all adopters (+EUR 30 each), everyone
    # after is a non-adopter (-EUR 0.50 each). So profit peaks at exactly
    # 10 contacts (1%) and falls after, even though cumulative precision at
    # 2% (50%) is still far above the 1.67% break-even.
    y = np.zeros(1000, dtype=int)
    y[:10] = 1
    scores = -np.arange(1000, dtype=float)
    curve = profit_curve(y, scores, budget_fracs=[0.005, 0.01, 0.02])
    assert curve["profit_eur"].tolist() == pytest.approx([147.5, 295.0, 290.0])
    assert best_budget_frac(y, scores, min_campaign_size=1) == pytest.approx(0.01)


def test_exact_profit_curve_starts_at_zero_and_steps_per_contact():
    # K=0 -> 0; each adopter +EUR 29.50 net (30 - 0.50), each non-adopter -0.50.
    y = np.array([1, 0, 1])
    scores = np.array([0.9, 0.8, 0.1])
    assert exact_profit_curve(y, scores).tolist() == pytest.approx([0.0, 29.5, 29.0, 58.5])


def test_best_budget_is_zero_when_no_contact_can_pay():
    # Phone cost EUR 6 with no adopters at all: contacting anyone loses money.
    y = np.zeros(100, dtype=int)
    assert best_budget_frac(y, np.random.default_rng(0).random(100), cost_per_contact=6.0) == 0.0


def test_best_budget_can_be_everyone_when_break_even_is_below_base_rate():
    # 50% base rate, break-even 1.67%, and the lowest-scored customer is an
    # adopter: every stretch of the list pays, so the best list is everyone.
    y = np.array([0, 1] * 50)
    assert best_budget_frac(y, -np.arange(100, dtype=float), min_campaign_size=1) == pytest.approx(1.0)


def test_best_budget_ignores_tiny_lucky_lists_below_the_floor():
    # Top 2 customers include 1 adopter (50% precision), then 998 non-adopters.
    # Without a floor the argmax picks that 2-row list; with a floor of 100
    # no real campaign pays, so the answer is "don't contact anyone".
    y = np.zeros(1000, dtype=int)
    y[0] = 1
    scores = -np.arange(1000, dtype=float)
    assert best_budget_frac(y, scores, min_campaign_size=1) == pytest.approx(0.001)
    assert best_budget_frac(y, scores, min_campaign_size=100) == 0.0


def test_sensitivity_sweep_has_one_row_per_scenario():
    rng = np.random.default_rng(0)
    y = (rng.random(500) < 0.05).astype(int)
    scores = y + rng.random(500)
    segment = rng.random(500) < 0.1
    sweep = sensitivity_sweep(y, scores, y, scores, segment)
    assert len(sweep) == 2 * 3 * 4
    assert not sweep.duplicated(["channel", "value_per_adoption", "uplift"]).any()


def test_compare_strategies_scores_model_at_the_segments_list_size():
    y = np.array([1, 0, 0, 0, 1, 0, 0, 0, 0, 0])
    scores = np.linspace(1, 0, 10)
    segment = np.array([False, False, False, True, True, True, False, False, False, False])
    table = compare_strategies(y, scores, segment, chosen_budget_frac=0.1).set_index("strategy")
    assert table.loc["segment_rule", "n_contacted"] == 3
    assert table.loc["model_top_k @ segment's list size", "n_contacted"] == 3
    assert table.loc["model_top_k @ val-chosen budget", "n_contacted"] == 1
    assert table.loc["contact_everyone", "n_contacted"] == 10


def test_in_segment_matches_phase3_definition():
    df = pd.DataFrame({
        "product_count_prev": [1, 1, 2, 1, 1, 1],
        "activity_index": [1, 1, 1, 0, 1, 1],
        "age_years": [40, 64, 40, 40, 30, 50],
        "segmento_top": [0, 0, 0, 0, 0, 1],
        "segmento_particulares": [1, 1, 1, 1, 1, 0],
        "segmento_universitario": [0, 0, 0, 0, 0, 0],
        "segmento_missing": [0, 0, 0, 0, 0, 0],
    })
    # Only the first two rows qualify: row 2 has 2 products, row 3 is
    # inactive, row 4 is 30 (outside 35-64), row 5 is `top`, not particulares.
    assert in_segment(df).tolist() == [True, True, False, False, False, False]

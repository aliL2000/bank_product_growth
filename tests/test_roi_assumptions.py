"""Unit tests for roi_assumptions.py's break-even and profit helpers, with
hand-computable expected values."""

import pytest

from models.roi_assumptions import break_even_precision, simulated_profit


def test_base_case_break_even_is_one_point_six_seven_percent():
    # 0.50 / (0.20 * 150) = 0.01667 - the number quoted in decision record 005.
    assert break_even_precision() == pytest.approx(0.016667, abs=1e-6)


def test_phone_break_even_is_above_the_models_best_precision():
    # 6.00 / (0.20 * 150) = 20% - above the ~8.7% best test precision, which
    # is why phone is unprofitable at any budget in the base case.
    assert break_even_precision(cost_per_contact=6.00) == pytest.approx(0.20)


def test_profit_is_zero_exactly_at_break_even_precision():
    n = 10_000
    p = break_even_precision()
    assert simulated_profit(n, p * n) == pytest.approx(0.0, abs=1e-9)


def test_profit_hand_computed_example():
    # 1,000 contacts, 50 adopters: 0.2 * 50 * 150 - 1,000 * 0.5 = 1,500 - 500.
    assert simulated_profit(1_000, 50) == pytest.approx(1_000.0)


def test_contact_everyone_at_base_rate_loses_money():
    # Test's overall adoption rate is 0.478%, below the 1.67% break-even.
    n = 1_000_000
    assert simulated_profit(n, 0.00478 * n) < 0

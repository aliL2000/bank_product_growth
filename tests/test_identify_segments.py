"""Unit tests for identify_segments.py's grouping/ranking helpers, on small
synthetic data with hand-computable expected values."""

import numpy as np
import pandas as pd
import pytest

from models.identify_segments import (
    bucket_product_count,
    label_segmento,
    rank_underserved_segments,
    wilson_lower_bound,
)


def test_wilson_lower_bound_matches_a_known_reference_value():
    # x=3, n=10 (phat=0.3): textbook 95% Wilson interval is approximately
    # (0.108, 0.603) - checking the lower bound against that reference.
    lower = wilson_lower_bound(np.array([3.0]), np.array([10.0]))
    assert lower[0] == pytest.approx(0.108, abs=0.001)


def test_wilson_lower_bound_is_below_the_raw_rate():
    # the interval should always sit below the point estimate (phat=0.5
    # here) - a sanity check on the formula's direction, not its exact value.
    phat_input = np.array([5.0])
    n = np.array([10.0])
    lower = wilson_lower_bound(phat_input, n)
    assert lower[0] < 0.5


def test_wilson_lower_bound_tightens_as_n_grows_at_the_same_rate():
    # same observed rate (10%), but 10x the sample size - more evidence
    # should narrow the gap between the raw rate and the lower bound.
    small_n = wilson_lower_bound(np.array([10.0]), np.array([100.0]))
    large_n = wilson_lower_bound(np.array([100.0]), np.array([1000.0]))
    assert (0.10 - large_n[0]) < (0.10 - small_n[0])


def test_label_segmento_picks_the_matching_one_hot_column():
    df = pd.DataFrame({
        "segmento_top": [1, 0, 0, 0],
        "segmento_particulares": [0, 1, 0, 0],
        "segmento_universitario": [0, 0, 1, 0],
    })
    labels = label_segmento(df)
    assert list(labels) == ["top", "particulares", "universitario", "missing"]


def test_bucket_product_count_splits_into_0_1_2plus():
    counts = pd.Series([0, 1, 2, 5, 0, 1])
    buckets = bucket_product_count(counts)
    assert list(buckets.astype(str)) == ["0", "1", "2+", "2+", "0", "1"]


def test_rank_underserved_segments_excludes_the_2plus_tier():
    stats = pd.DataFrame({
        "product_tier": ["0", "1", "2+"],
        "segmento_label": ["particulares"] * 3,
        "activity_label": ["active"] * 3,
        "age_band": ["35-44"] * 3,
        "n": [10000, 10000, 10000],
        "adoptions": [50, 50, 50],
    })
    stats["observed_rate"] = stats["adoptions"] / stats["n"]
    stats["wilson_lower"] = wilson_lower_bound(stats["adoptions"].to_numpy(), stats["n"].to_numpy())

    ranked = rank_underserved_segments(stats, overall_rate=0.005, min_n=1000)

    assert set(ranked["product_tier"]) == {"0", "1"}


def test_rank_underserved_segments_drops_groups_below_min_n():
    stats = pd.DataFrame({
        "product_tier": ["0", "0"],
        "segmento_label": ["particulares", "particulares"],
        "activity_label": ["active", "active"],
        "age_band": ["35-44", "45-54"],
        "n": [100, 10000],
        "adoptions": [5, 50],
    })
    stats["observed_rate"] = stats["adoptions"] / stats["n"]
    stats["wilson_lower"] = wilson_lower_bound(stats["adoptions"].to_numpy(), stats["n"].to_numpy())

    ranked = rank_underserved_segments(stats, overall_rate=0.005, min_n=1000)

    assert len(ranked) == 1
    assert ranked.iloc[0]["age_band"] == "45-54"


def test_rank_underserved_segments_favors_reliable_over_small_and_lucky():
    # group A: tiny sample, high raw rate (8/100 = 8%) that could easily be
    # luck. group B: large sample, lower raw rate (550/10000 = 5.5%) backed
    # by far more evidence. Ranking by the raw rate would put A first;
    # ranking by the Wilson lower bound (the whole point of using it) puts
    # B first instead, since A's interval is much wider given so little
    # data (lower bounds: A=4.1%, B=5.1%, computed by hand below).
    stats = pd.DataFrame({
        "product_tier": ["0", "0"],
        "segmento_label": ["particulares", "particulares"],
        "activity_label": ["active", "active"],
        "age_band": ["lucky_and_small", "reliable_and_large"],
        "n": [100, 10000],
        "adoptions": [8, 550],
    })
    stats["observed_rate"] = stats["adoptions"] / stats["n"]
    stats["wilson_lower"] = wilson_lower_bound(stats["adoptions"].to_numpy(), stats["n"].to_numpy())

    assert stats.iloc[0]["observed_rate"] > stats.iloc[1]["observed_rate"]  # A's raw rate is higher

    ranked = rank_underserved_segments(stats, overall_rate=0.005, min_n=50)

    assert ranked.iloc[0]["age_band"] == "reliable_and_large"

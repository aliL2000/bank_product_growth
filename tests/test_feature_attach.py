"""Merge-safety unit tests for each Group's attach_profile() - the t-1
point-in-time join shared by all three Phase 2 feature-build scripts. This
targets the [no-tests-on-label-logic] audit finding's "no merge-safety
assertions (e.g. row count unchanged after a left join)" half, using small
synthetic frames instead of the real 12M-row files.

Each attach_profile() is a left join keyed on (ncodpers, prev_month) against
a profile keyed on (ncodpers, month). Every test below checks the two things
that matter for correctness: (1) the join never changes the row count (the
assertion now also lives in the scripts themselves), and (2) a customer with
no matching t-1 profile row gets NaN, not a value borrowed from elsewhere.
"""

import pandas as pd

from features.build_features_demographics import attach_profile as attach_demographics
from features.build_features_product_count import attach_profile as attach_product_count
from features.build_features_tenure_activity import attach_profile as attach_tenure_activity


def _split_df(ncodpers_prev_month_pairs):
    ncodpers, prev_months = zip(*ncodpers_prev_month_pairs)
    return pd.DataFrame(
        {
            "ncodpers": list(ncodpers),
            "prev_month": pd.PeriodIndex(prev_months, freq="M"),
        }
    )


def test_tenure_activity_attach_matches_and_preserves_row_count():
    split_df = _split_df([(1, "2015-01"), (2, "2015-01")])  # customer 2 has no profile row
    profile = pd.DataFrame(
        {
            "ncodpers": [1],
            "month": pd.PeriodIndex(["2015-01"], freq="M"),
            "antiguedad": [12.0],
            "ind_actividad_cliente": [1.0],
        }
    )

    merged = attach_tenure_activity(split_df, profile)

    assert len(merged) == len(split_df)
    matched = merged.set_index("ncodpers")
    assert matched.loc[1, "antiguedad"] == 12.0
    assert pd.isna(matched.loc[2, "antiguedad"])


def test_product_count_attach_matches_and_preserves_row_count():
    split_df = _split_df([(1, "2015-01"), (2, "2015-01")])
    profile = pd.DataFrame(
        {
            "ncodpers": [1],
            "month": pd.PeriodIndex(["2015-01"], freq="M"),
            "ind_cco_fin_ult1": [1],
        }
    )

    merged = attach_product_count(split_df, profile)

    assert len(merged) == len(split_df)
    matched = merged.set_index("ncodpers")
    assert matched.loc[1, "ind_cco_fin_ult1"] == 1
    assert pd.isna(matched.loc[2, "ind_cco_fin_ult1"])


def test_demographics_attach_matches_and_preserves_row_count():
    split_df = _split_df([(1, "2015-01"), (2, "2015-01")])
    profile = pd.DataFrame(
        {
            "ncodpers": [1],
            "month": pd.PeriodIndex(["2015-01"], freq="M"),
            "age": [35.0],
            "sexo": ["H"],
            "renta": [90000.0],
            "segmento": ["particulares"],
        }
    )

    merged = attach_demographics(split_df, profile)

    assert len(merged) == len(split_df)
    matched = merged.set_index("ncodpers")
    assert matched.loc[1, "age"] == 35.0
    assert pd.isna(matched.loc[2, "age"])

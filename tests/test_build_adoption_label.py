"""Unit tests for the adoption label's merge-based lag join (build_label).

This is the single point of failure the /audit flagged as untested
([no-tests-on-label-logic] in docs/audit_log.md) - everything downstream
(split, features, model) inherits whatever this function gets wrong. Uses a
small synthetic dataset instead of the real 13M-row file so the test is fast
and each expected outcome is known by construction.
"""

import pandas as pd

from features.build_adoption_label import TARGET_COL, build_label


def _make_df(rows):
    """rows: list of (ncodpers, month_str, flag)."""
    df = pd.DataFrame(rows, columns=["ncodpers", "month_str", TARGET_COL])
    df["month"] = pd.PeriodIndex(df["month_str"], freq="M")
    df["fecha_dato"] = df["month"].dt.to_timestamp()
    return df[["ncodpers", "fecha_dato", "month", TARGET_COL]]


def _lookup(result, ncodpers, month_str):
    row = result[(result["ncodpers"] == ncodpers) & (result["month"] == pd.Period(month_str, "M"))]
    assert len(row) == 1, f"expected exactly one row for ({ncodpers}, {month_str})"
    return row.iloc[0]


def test_adoption_when_gained_product():
    """Non-holder in month t-1, holder in month t -> adoption True."""
    df = _make_df([(1, "2015-01", 0), (1, "2015-02", 1)])
    result = build_label(df)
    row = _lookup(result, 1, "2015-02")
    assert row["label_defined"]
    assert row["adoption"] == True  # noqa: E712 (nullable boolean, not `is True`)


def test_no_adoption_when_already_holder():
    """Already held the product at t-1 -> not an adoption event, even though
    the flag is 1 in both months (this is the eligibility distinction behind
    docs/decisions/003-eligibility-filter.md)."""
    df = _make_df([(2, "2015-01", 1), (2, "2015-02", 1)])
    result = build_label(df)
    row = _lookup(result, 2, "2015-02")
    assert row["label_defined"]
    assert row["adoption"] == False  # noqa: E712


def test_no_adoption_when_stays_non_holder():
    """Non-holder at t-1 and still a non-holder at t -> not an adoption."""
    df = _make_df([(3, "2015-01", 0), (3, "2015-02", 0)])
    result = build_label(df)
    row = _lookup(result, 3, "2015-02")
    assert row["label_defined"]
    assert row["adoption"] == False  # noqa: E712


def test_label_undefined_with_no_prior_row():
    """A customer's first observed month has no t-1 row to compare against,
    so the label must be undefined (NA), not silently treated as False."""
    df = _make_df([(1, "2015-01", 0), (1, "2015-02", 1)])
    result = build_label(df)
    row = _lookup(result, 1, "2015-01")
    assert not row["label_defined"]
    assert pd.isna(row["adoption"])


def test_label_undefined_across_a_gap_month():
    """A customer with a gap (present in 2015-01 and 2015-03 but missing
    2015-02) must NOT get a t-1 value borrowed from 2015-01 for the 2015-03
    row - the merge key is calendar month, not row position, precisely to
    avoid this kind of silent mislabeling (see docs/concepts_log.md)."""
    df = _make_df([(4, "2015-01", 0), (4, "2015-03", 1)])
    result = build_label(df)
    row = _lookup(result, 4, "2015-03")
    assert not row["label_defined"]
    assert pd.isna(row["adoption"])


def test_merge_preserves_row_count():
    """The lag join is a left join keyed on (ncodpers, month) - it must never
    duplicate or drop rows from the input."""
    df = _make_df(
        [
            (1, "2015-01", 0),
            (1, "2015-02", 1),
            (2, "2015-01", 1),
            (2, "2015-02", 1),
        ]
    )
    result = build_label(df)
    assert len(result) == len(df)

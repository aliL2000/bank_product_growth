"""Merge-safety unit tests for build_modeling_table.py's attach()/assemble(),
following the same pattern as tests/test_feature_attach.py: small synthetic
frames instead of the real 12M-row files, checking that joins never change
row counts and that an unmatched row gets NaN rather than a borrowed value.
"""

import pandas as pd
import pytest

from features.build_modeling_table import assemble, attach


def _key_df(rows, **extra_cols):
    ncodpers, fecha_dato = zip(*rows)
    df = pd.DataFrame(
        {"ncodpers": list(ncodpers), "fecha_dato": pd.to_datetime(list(fecha_dato))}
    )
    for col, values in extra_cols.items():
        df[col] = values
    return df


def test_attach_preserves_row_count_and_fills_unmatched_with_nan():
    base = _key_df([(1, "2015-02-01"), (2, "2015-02-01")], split=["train", "train"])
    other = _key_df([(1, "2015-02-01")], value=[10.0])  # customer 2 has no row

    merged = attach(base, other, "test feature")

    assert len(merged) == len(base)
    matched = merged.set_index("ncodpers")
    assert matched.loc[1, "value"] == 10.0
    assert pd.isna(matched.loc[2, "value"])


def test_attach_raises_on_duplicate_key_in_other():
    base = _key_df([(1, "2015-02-01")], split=["train"])
    other = _key_df([(1, "2015-02-01"), (1, "2015-02-01")], value=[10.0, 20.0])

    with pytest.raises(Exception):
        attach(base, other, "test feature")


def test_assemble_joins_label_and_all_three_feature_groups():
    base = _key_df([(1, "2015-02-01"), (2, "2015-02-01")], split=["train", "train"])
    labels = _key_df([(1, "2015-02-01"), (2, "2015-02-01")], adoption=[True, False])
    tenure_activity = _key_df([(1, "2015-02-01"), (2, "2015-02-01")], tenure_months=[12.0, 3.0])
    product_count = _key_df([(1, "2015-02-01"), (2, "2015-02-01")], product_count_prev=[2, 0])
    demographics = _key_df([(1, "2015-02-01"), (2, "2015-02-01")], age_years=[35.0, 22.0])

    df = assemble(base, labels, tenure_activity, product_count, demographics)

    assert len(df) == len(base)
    assert set(["adoption", "tenure_months", "product_count_prev", "age_years"]) <= set(df.columns)
    assert df["adoption"].notna().all()

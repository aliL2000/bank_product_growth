"""Unit test for the time-respecting train/val split assignment.

Checks build_split() puts each labeled month on the correct side of the
train/val boundary (docs/decisions/002-train-val-split.md: last 3 labeled
months = val, everything earlier = train) using a small synthetic frame
instead of the real 12M-row split.
"""

import pandas as pd

from features.train_val_split import VAL_MONTHS, build_split


def test_val_months_assigned_to_val():
    months = sorted(VAL_MONTHS)
    df = pd.DataFrame(
        {
            "ncodpers": [1] * len(months),
            "month": pd.PeriodIndex(months, freq="M"),
        }
    )
    df["fecha_dato"] = df["month"].dt.to_timestamp()

    result = build_split(df)

    assert (result["split"] == "val").all()


def test_earlier_months_assigned_to_train():
    df = pd.DataFrame(
        {
            "ncodpers": [1, 1],
            "month": pd.PeriodIndex(["2015-02", "2016-02"], freq="M"),
        }
    )
    df["fecha_dato"] = df["month"].dt.to_timestamp()

    result = build_split(df)

    assert (result["split"] == "train").all()


def test_split_column_is_only_train_or_val():
    df = pd.DataFrame(
        {
            "ncodpers": [1, 1, 1],
            "month": pd.PeriodIndex(["2015-02", "2016-03", "2016-05"], freq="M"),
        }
    )
    df["fecha_dato"] = df["month"].dt.to_timestamp()

    result = build_split(df)

    assert set(result["split"]) <= {"train", "val"}
    assert list(result["split"]) == ["train", "val", "val"]

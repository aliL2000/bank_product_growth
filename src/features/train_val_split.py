"""Time-respecting train/val split over the credit card adoption label.

Validation = the last 3 labeled months (2016-03, 2016-04, 2016-05); train =
every earlier labeled month (2015-02 through 2016-02). Rows with no defined
label (2015-01, and later gap rows for customers with no prior-month row) are
dropped here since they can't be used for either training or evaluation.
Rows where the customer already held a credit card at t-1 are also dropped
here - see docs/decisions/003-eligibility-filter.md for why the modeling
population is restricted to eligible non-holders.

See docs/concepts_log.md for why this is a period-based split (not a
customer-holdout split) and why no gap month is needed between train and val.
"""

from pathlib import Path

import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
LABELS_PATH = PROCESSED_DIR / "adoption_labels_tjcr.csv"
OUTPUT_PATH = PROCESSED_DIR / "train_val_split.csv"

VAL_MONTHS = {"2016-03", "2016-04", "2016-05"}


def load_labeled() -> pd.DataFrame:
    """Load only the labeled, eligible rows, with memory-light dtypes.

    Eligible = label_defined (had a prior-month row) AND prev_flag == 0
    (didn't already hold a credit card at t-1). Excluding already-holders
    keeps the negative class meaning "chose not to adopt" rather than
    "structurally couldn't" - see docs/decisions/003-eligibility-filter.md.
    """
    df = pd.read_csv(
        LABELS_PATH,
        usecols=["ncodpers", "fecha_dato", "month", "prev_flag", "label_defined", "adoption"],
        dtype={
            "ncodpers": "int32",
            "fecha_dato": "str",
            "month": "str",
            "prev_flag": "float32",
            "label_defined": "bool",
            "adoption": "str",
        },
    )
    already_holder = (df["prev_flag"] == 1).sum()
    print(f"dropping {already_holder} already-holder rows (prev_flag == 1) before split")
    return df[df["label_defined"] & (df["prev_flag"] == 0)].copy()


def build_split(labeled: pd.DataFrame) -> pd.DataFrame:
    labeled["split"] = labeled["month"].apply(lambda m: "val" if m in VAL_MONTHS else "train")
    return labeled[["ncodpers", "fecha_dato", "split"]]


def summarize(labeled: pd.DataFrame) -> None:
    labeled = labeled.copy()
    labeled["adoption"] = labeled["adoption"] == "True"

    by_split = labeled.groupby("split")["adoption"].agg(["size", "sum"])
    by_split["rate_pct"] = 100 * by_split["sum"] / by_split["size"]
    print("rows and adoption rate by split:")
    print(by_split.rename(columns={"size": "rows", "sum": "adoptions"}))

    months_by_split = labeled.groupby("split")["month"].agg(["min", "max", "nunique"])
    print("\nmonth range by split:")
    print(months_by_split)


if __name__ == "__main__":
    labeled = load_labeled()
    split_df = build_split(labeled)
    summarize(labeled)

    split_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nwrote {len(split_df)} rows to {OUTPUT_PATH}")

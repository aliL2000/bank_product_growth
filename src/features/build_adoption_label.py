"""Build the credit card (ind_tjcr_fin_ult1, "Service A") adoption label.

Adoption event for customer c in month t: held 0 in month t-1, holds 1 in
month t. See docs/decisions/001-service-a-product-choice.md for why credit
card was chosen, and docs/concepts_log.md for why this uses a merge-based
lag instead of a naive positional shift.
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
TRAIN_PATH = RAW_DIR / "train_ver2.csv"
OUTPUT_PATH = PROCESSED_DIR / "adoption_labels_tjcr.parquet"

TARGET_COL = "ind_tjcr_fin_ult1"


def load_slim() -> pd.DataFrame:
    """Load only the columns needed for label construction, with memory-light
    dtypes. Unlike the full-file scan in load_data.py (which needed chunking
    because it touched all 48 columns), pruning to 3 columns keeps this small
    enough to load in one shot."""
    df = pd.read_csv(
        TRAIN_PATH,
        usecols=["fecha_dato", "ncodpers", TARGET_COL],
        dtype={"ncodpers": "int32", TARGET_COL: "int8"},
        parse_dates=["fecha_dato"],
    )
    df["month"] = df["fecha_dato"].dt.to_period("M")
    return df


def build_label(df: pd.DataFrame) -> pd.DataFrame:
    """Attach each row's *previous month's* flag for the same customer via an
    explicit (ncodpers, month) merge, then derive the adoption label."""
    lookup = df[["ncodpers", "month", TARGET_COL]].rename(
        columns={"month": "lookup_month", TARGET_COL: "prev_flag"}
    )
    df = df.copy()
    df["prev_month"] = df["month"] - 1

    merged = df.merge(
        lookup,
        left_on=["ncodpers", "prev_month"],
        right_on=["ncodpers", "lookup_month"],
        how="left",
    )
    assert len(merged) == len(df), (
        f"left join changed row count ({len(df)} -> {len(merged)}) - "
        "lookup must have at most one row per (ncodpers, month)"
    )

    merged["label_defined"] = merged["prev_flag"].notna()
    adoption = (merged["prev_flag"] == 0) & (merged[TARGET_COL] == 1)
    merged["adoption"] = adoption.astype("boolean")
    merged.loc[~merged["label_defined"], "adoption"] = pd.NA

    return merged[
        ["ncodpers", "fecha_dato", "month", TARGET_COL, "prev_flag", "label_defined", "adoption"]
    ]


def summarize(labeled: pd.DataFrame) -> None:
    total = len(labeled)
    defined = labeled["label_defined"].sum()
    print(f"total rows: {total}")
    print(f"rows with a defined label (had a prior-month row): {defined} ({defined/total:.1%})")
    print(f"rows with no prior-month row (new customer / gap): {total - defined}")

    defined_rows = labeled[labeled["label_defined"]]
    n_events = defined_rows["adoption"].sum()
    n_eligible = (defined_rows["prev_flag"] == 0).sum()
    print(f"\nadoption events (prev=0 -> current=1): {n_events}")
    print(f"non-holders in month t-1 (eligible population): {n_eligible}")
    print(f"adoption rate among eligible non-holders: {n_events / n_eligible:.4%}")

    print("\nadoption events by month:")
    by_month = defined_rows.groupby("month")["adoption"].sum()
    print(by_month)


if __name__ == "__main__":
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    slim = load_slim()
    print(f"slim frame memory: {slim.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

    labeled = build_label(slim)
    summarize(labeled)

    labeled.to_parquet(OUTPUT_PATH, index=False)
    print(f"\nwrote {len(labeled)} rows to {OUTPUT_PATH}")

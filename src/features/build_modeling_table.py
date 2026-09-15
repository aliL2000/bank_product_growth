"""Assemble the final modeling-ready table for Phase 2 baseline models.

Joins the eligible labeled population (data/processed/train_val_split.parquet)
to the adoption label and all three Phase 2 feature groups (tenure/activity,
product count, demographics), all keyed on (ncodpers, fecha_dato). Every
feature file was already built against this exact same population - one row
per (ncodpers, fecha_dato) - so each join here is a row-count-preserving
lookup, not a fan-out, same as the t-1 profile joins inside each feature
script (see docs/concepts_log.md's "Point-in-time correctness" entry).

Output is a single wide table with a `split` column, rather than three
separate train/val/test files - keeps "what counts as train/val/test" living
in one place (train_val_split.py) instead of needing to be re-applied
downstream.
"""

from pathlib import Path

import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
SPLIT_PATH = PROCESSED_DIR / "train_val_split.parquet"
LABELS_PATH = PROCESSED_DIR / "adoption_labels_tjcr.parquet"
TENURE_ACTIVITY_PATH = PROCESSED_DIR / "features_tenure_activity.parquet"
PRODUCT_COUNT_PATH = PROCESSED_DIR / "features_product_count.parquet"
DEMOGRAPHICS_PATH = PROCESSED_DIR / "features_demographics.parquet"
OUTPUT_PATH = PROCESSED_DIR / "modeling_table.parquet"

KEY = ["ncodpers", "fecha_dato"]


def load_base() -> pd.DataFrame:
    """The eligible, labeled population with its train/val/test tag."""
    return pd.read_parquet(SPLIT_PATH)


def load_labels() -> pd.DataFrame:
    return pd.read_parquet(LABELS_PATH, columns=KEY + ["adoption"])


def load_feature_file(path: Path) -> pd.DataFrame:
    """Load a Phase 2 feature file, dropping its repeated `split` column so
    the merge below can't collide on a shared non-key column name."""
    return pd.read_parquet(path).drop(columns=["split"])


def attach(base: pd.DataFrame, other: pd.DataFrame, name: str) -> pd.DataFrame:
    """Left-join `other` onto `base` on (ncodpers, fecha_dato).

    validate="one_to_one" makes pandas itself check that neither side has a
    duplicate key - a stronger, built-in version of the manual row-count
    assert used in the earlier feature scripts. Row count is still asserted
    explicitly too, since validate only checks *keys*, not that every base
    row actually found a match.
    """
    merged = base.merge(other, on=KEY, how="left", validate="one_to_one")
    assert len(merged) == len(base), (
        f"{name} join changed row count ({len(base)} -> {len(merged)})"
    )
    new_cols = other.columns.difference(KEY)
    unmatched = merged[list(new_cols)].isna().any(axis=1).mean()
    print(f"{name}: {unmatched:.3%} of rows had no match")
    return merged


def assemble(
    base: pd.DataFrame,
    labels: pd.DataFrame,
    tenure_activity: pd.DataFrame,
    product_count: pd.DataFrame,
    demographics: pd.DataFrame,
) -> pd.DataFrame:
    df = attach(base, labels, "label")
    df = attach(df, tenure_activity, "tenure/activity")
    df = attach(df, product_count, "product count")
    df = attach(df, demographics, "demographics")
    assert df["adoption"].notna().all(), (
        "every row in the eligible split must have a defined adoption label"
    )
    return df


def summarize(df: pd.DataFrame) -> None:
    print(f"\nassembled table: {len(df):,} rows, {df.shape[1]} columns")
    print(f"columns: {list(df.columns)}")
    by_split = df.groupby("split")["adoption"].agg(["size", "sum"])
    by_split["rate_pct"] = 100 * by_split["sum"] / by_split["size"]
    print("\nrows and adoption rate by split:")
    print(by_split.rename(columns={"size": "rows", "sum": "adoptions"}))


if __name__ == "__main__":
    base = load_base()
    labels = load_labels()
    tenure_activity = load_feature_file(TENURE_ACTIVITY_PATH)
    product_count = load_feature_file(PRODUCT_COUNT_PATH)
    demographics = load_feature_file(DEMOGRAPHICS_PATH)

    df = assemble(base, labels, tenure_activity, product_count, demographics)
    summarize(df)

    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"\nwrote {len(df)} rows to {OUTPUT_PATH}")

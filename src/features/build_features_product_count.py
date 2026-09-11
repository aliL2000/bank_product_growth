"""Phase 2, Group 2 feature: product count.

Joins each labeled (customer, month t) row in data/processed/train_val_split.csv
to that customer's product-holding flags as of month *t-1*, using the same
point-in-time merge-key trick as Group 1 (see docs/concepts_log.md's
"Point-in-time correctness" entry), and sums them into a single
`product_count_prev` feature — a proxy for general engagement/cross-sell
propensity, independent of any single product.

`ind_tjcr_fin_ult1` (the Service A target) is deliberately excluded from the
sum: for eligible rows it's always 0 at t-1 (that's the eligibility
condition), and for the non-eligible already-holder rows in the split it
would just re-encode `adoption`'s trivial False outcome as part of the
count. Excluding it keeps product_count a measure of *other* engagement.

Two of the 24 raw flags (`ind_nomina_ult1`, `ind_nom_pens_ult1` - payroll and
payroll pension) are missing for 16,063 rows each (0.12%), a known quirk of
this dataset; filled with 0 (assume "not held" rather than invent a
per-column missing flag) since the effect on a 23-column sum is negligible.
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
TRAIN_PATH = RAW_DIR / "train_ver2.csv"
SPLIT_PATH = PROCESSED_DIR / "train_val_split.csv"
OUTPUT_PATH = PROCESSED_DIR / "features_product_count.csv"

TARGET_COL = "ind_tjcr_fin_ult1"
ALL_PRODUCT_COLS = [
    "ind_ahor_fin_ult1", "ind_aval_fin_ult1", "ind_cco_fin_ult1",
    "ind_cder_fin_ult1", "ind_cno_fin_ult1", "ind_ctju_fin_ult1",
    "ind_ctma_fin_ult1", "ind_ctop_fin_ult1", "ind_ctpp_fin_ult1",
    "ind_deco_fin_ult1", "ind_deme_fin_ult1", "ind_dela_fin_ult1",
    "ind_ecue_fin_ult1", "ind_fond_fin_ult1", "ind_hip_fin_ult1",
    "ind_plan_fin_ult1", "ind_pres_fin_ult1", "ind_reca_fin_ult1",
    "ind_tjcr_fin_ult1", "ind_valo_fin_ult1", "ind_viv_fin_ult1",
    "ind_nomina_ult1", "ind_nom_pens_ult1", "ind_recibo_ult1",
]
COUNT_COLS = [c for c in ALL_PRODUCT_COLS if c != TARGET_COL]


def load_split() -> pd.DataFrame:
    """Load the labeled split, deriving month/prev_month from fecha_dato
    (train_val_split.csv doesn't carry a separate month column)."""
    df = pd.read_csv(
        SPLIT_PATH,
        dtype={"ncodpers": "int32", "split": "category"},
        parse_dates=["fecha_dato"],
    )
    df["month"] = df["fecha_dato"].dt.to_period("M")
    df["prev_month"] = df["month"] - 1
    return df


def load_profile() -> pd.DataFrame:
    """Load the 23 non-target product flags for every raw row, with missing
    values (ind_nomina_ult1 / ind_nom_pens_ult1 only) filled as 0."""
    usecols = ["fecha_dato", "ncodpers"] + COUNT_COLS
    dtype = {"ncodpers": "int32", **{c: "float32" for c in COUNT_COLS}}
    profile = pd.read_csv(TRAIN_PATH, usecols=usecols, dtype=dtype, parse_dates=["fecha_dato"])
    profile[COUNT_COLS] = profile[COUNT_COLS].fillna(0).astype("int8")
    profile["month"] = profile["fecha_dato"].dt.to_period("M")
    return profile[["ncodpers", "month"] + COUNT_COLS]


def attach_profile(split_df: pd.DataFrame, profile: pd.DataFrame) -> pd.DataFrame:
    lookup = profile.rename(columns={"month": "profile_month"})
    merged = split_df.merge(
        lookup,
        left_on=["ncodpers", "prev_month"],
        right_on=["ncodpers", "profile_month"],
        how="left",
    )
    matched = merged["profile_month"].notna().mean()
    print(f"rows matched to a t-1 profile row: {matched:.2%}")
    return merged


def build_product_count(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["product_count_missing"] = df["profile_month"].isna()
    # unmatched rows (no t-1 profile row) get a count of 0 by construction of fillna below
    df[COUNT_COLS] = df[COUNT_COLS].fillna(0)
    df["product_count_prev"] = df[COUNT_COLS].sum(axis=1).astype("int8")
    return df


def summarize(df: pd.DataFrame) -> None:
    print(f"\nproduct_count_missing rate: {df['product_count_missing'].mean():.3%}")
    print("\nproduct_count_prev distribution (train split):")
    print(df.loc[df["split"] == "train", "product_count_prev"].value_counts().sort_index())
    print("\nmean product_count_prev by split (sanity check, not leakage-sensitive):")
    print(df.groupby("split", observed=True)["product_count_prev"].mean())


if __name__ == "__main__":
    split_df = load_split()
    profile = load_profile()

    merged = attach_profile(split_df, profile)
    del profile

    features = build_product_count(merged)
    summarize(features)

    out = features[["ncodpers", "fecha_dato", "split", "product_count_prev", "product_count_missing"]]
    out.to_csv(OUTPUT_PATH, index=False)
    print(f"\nwrote {len(out)} rows to {OUTPUT_PATH}")

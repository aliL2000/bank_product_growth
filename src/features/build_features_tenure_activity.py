"""Phase 2, Group 1 features: tenure and activity index.

Joins each labeled (customer, month t) row in data/processed/train_val_split.csv
to that customer's tenure (`antiguedad`) and activity index
(`ind_actividad_cliente`) as of month *t-1*, using the same point-in-time
merge-key trick as the label build and EDA (see docs/concepts_log.md's
"Point-in-time correctness" entry). Cleans the bad-data patterns flagged in
`reports/01_eda_findings.md` (antiguedad's -999999 placeholder and string
"NA") and imputes missing values using train-only statistics, per the
leakage caveat in docs/decisions/002-train-val-split.md.
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
TRAIN_PATH = RAW_DIR / "train_ver2.csv"
SPLIT_PATH = PROCESSED_DIR / "train_val_split.parquet"
OUTPUT_PATH = PROCESSED_DIR / "features_tenure_activity.parquet"

PROFILE_COLS = ["fecha_dato", "ncodpers", "antiguedad", "ind_actividad_cliente"]


def load_split() -> pd.DataFrame:
    """Load the labeled split, deriving month/prev_month from fecha_dato
    (train_val_split.parquet doesn't carry a separate month column)."""
    df = pd.read_parquet(SPLIT_PATH)
    df["month"] = df["fecha_dato"].dt.to_period("M")
    df["prev_month"] = df["month"] - 1
    return df


def load_profile() -> pd.DataFrame:
    """Load tenure + activity index for every raw row, cleaned to numeric.

    antiguedad is fixed-width, space-padded text with a literal "NA" string
    for missing, plus a known -999999 sentinel for bad/unknown tenure (see
    reports/01_eda_findings.md's data-quality notes) - both become NaN.
    """
    profile = pd.read_csv(
        TRAIN_PATH,
        usecols=PROFILE_COLS,
        dtype={
            "ncodpers": "int32",
            "antiguedad": "str",
            "ind_actividad_cliente": "float32",
        },
        parse_dates=["fecha_dato"],
    )
    profile["antiguedad"] = pd.to_numeric(
        profile["antiguedad"].str.strip(), errors="coerce"
    ).astype("float32")
    profile.loc[profile["antiguedad"] == -999999, "antiguedad"] = np.nan
    profile["month"] = profile["fecha_dato"].dt.to_period("M")
    return profile[["ncodpers", "month", "antiguedad", "ind_actividad_cliente"]]


def attach_profile(split_df: pd.DataFrame, profile: pd.DataFrame) -> pd.DataFrame:
    lookup = profile.rename(columns={"month": "profile_month"})
    merged = split_df.merge(
        lookup,
        left_on=["ncodpers", "prev_month"],
        right_on=["ncodpers", "profile_month"],
        how="left",
    )
    assert len(merged) == len(split_df), (
        f"left join changed row count ({len(split_df)} -> {len(merged)}) - "
        "profile must have at most one row per (ncodpers, month)"
    )
    matched = merged["profile_month"].notna().mean()
    print(f"rows matched to a t-1 profile row: {matched:.2%}")
    return merged


def impute_train_only(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing tenure/activity with statistics fit on the train split
    only, then applied to both splits - val must never influence the
    imputed value (docs/decisions/002-train-val-split.md). Also keeps an
    explicit *_missing flag, since "value was unknown" can itself be
    predictive and a model shouldn't be unable to tell it apart from a
    genuine value that happened to equal the imputed one.
    """
    df = df.copy()
    df["tenure_missing"] = df["antiguedad"].isna()
    df["activity_missing"] = df["ind_actividad_cliente"].isna()

    train_mask = df["split"] == "train"
    tenure_median = df.loc[train_mask, "antiguedad"].median()
    activity_mode = df.loc[train_mask, "ind_actividad_cliente"].mode().iloc[0]

    df["tenure_months"] = df["antiguedad"].fillna(tenure_median).astype("float32")
    df["activity_index"] = (
        df["ind_actividad_cliente"].fillna(activity_mode).astype("float32")
    )

    print(f"train-only tenure median used for imputation: {tenure_median:.1f} months")
    print(f"train-only activity mode used for imputation: {activity_mode:.0f}")
    return df


def summarize(df: pd.DataFrame) -> None:
    print(f"\ntenure_missing rate: {df['tenure_missing'].mean():.3%}")
    print(f"activity_missing rate: {df['activity_missing'].mean():.3%}")
    print("\nmean feature value by split (sanity check, not leakage-sensitive):")
    print(df.groupby("split", observed=True)[["tenure_months", "activity_index"]].mean())


if __name__ == "__main__":
    split_df = load_split()
    profile = load_profile()

    merged = attach_profile(split_df, profile)
    del profile

    features = impute_train_only(merged)
    summarize(features)

    out = features[
        [
            "ncodpers",
            "fecha_dato",
            "split",
            "tenure_months",
            "tenure_missing",
            "activity_index",
            "activity_missing",
        ]
    ]
    out.to_parquet(OUTPUT_PATH, index=False)
    print(f"\nwrote {len(out)} rows to {OUTPUT_PATH}")

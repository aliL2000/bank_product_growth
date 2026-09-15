"""Phase 2, Group 3 features: demographics (age, sex, segmento, income).

Joins each labeled (customer, month t) row in data/processed/train_val_split.csv
to that customer's demographic attributes as of month *t-1*, using the same
point-in-time merge-key trick as Groups 1-2 (see docs/concepts_log.md's
"Point-in-time correctness" entry).

Cleaning/imputation decisions, each explored and justified in the working
session before writing this (see docs/concepts_log.md and the ROADMAP
working log for 2026-09-11 if writing this from scratch again):
- age: values > 100 (clearly implausible - max raw value was 164) become
  NaN before imputation; ages under 15 are left alone, since Spain's
  "junior" custodial accounts make young account holders real data, not an
  error. Also builds age_years_sq (age centered on the train mean, then
  squared) - a per-bin lift table (docs/audit_log.md,
  [correlation-yardstick-vs-nonmonotonic-feature]) showed adoption peaks
  around 45-50 and falls off on both sides, a shape a linear model can't
  capture from age_years alone.
- sexo / segmento: one-hot encoded categoricals, each with its own
  *_missing flag, same convention as Group 1's numeric *_missing flags.
- renta (income): imputed with a train-only median **grouped by segmento**
  rather than one flat global median (segmento medians range ~89k-142k,
  vs. one global ~102k for everyone) - a step up from Group 1's plain
  global-median imputation, since income genuinely varies by customer
  segment. Falls back to the global train median for the ~1.4% of rows
  where segmento itself is missing. A log-transformed renta_log is also
  built, since raw income is heavily right-skewed (mean ~135k vs. median
  ~102k, max ~29M) - needed for the logistic regression baseline coming up
  in Phase 2, harmless for LightGBM.
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
TRAIN_PATH = RAW_DIR / "train_ver2.csv"
SPLIT_PATH = PROCESSED_DIR / "train_val_split.parquet"
OUTPUT_PATH = PROCESSED_DIR / "features_demographics.parquet"

PROFILE_COLS = ["fecha_dato", "ncodpers", "age", "sexo", "renta", "segmento"]
AGE_MAX_PLAUSIBLE = 100
SEGMENTO_MAP = {
    "01 - TOP": "top",
    "02 - PARTICULARES": "particulares",
    "03 - UNIVERSITARIO": "universitario",
}


def load_split() -> pd.DataFrame:
    """Load the labeled split, deriving month/prev_month from fecha_dato
    (train_val_split.parquet doesn't carry a separate month column)."""
    df = pd.read_parquet(SPLIT_PATH)
    df["month"] = df["fecha_dato"].dt.to_period("M")
    df["prev_month"] = df["month"] - 1
    return df


def load_profile() -> pd.DataFrame:
    """Load age/sexo/renta/segmento for every raw row, cleaned to usable
    types. age is text like antiguedad, so it's coerced the same way; renta
    parses directly as numeric."""
    profile = pd.read_csv(
        TRAIN_PATH,
        usecols=PROFILE_COLS,
        dtype={
            "ncodpers": "int32",
            "age": "str",
            "sexo": "str",
            "renta": "float32",
            "segmento": "str",
        },
        parse_dates=["fecha_dato"],
    )
    profile["age"] = pd.to_numeric(profile["age"].str.strip(), errors="coerce").astype("float32")
    profile.loc[profile["age"] > AGE_MAX_PLAUSIBLE, "age"] = np.nan
    profile["segmento"] = profile["segmento"].str.strip().map(SEGMENTO_MAP)
    profile["month"] = profile["fecha_dato"].dt.to_period("M")
    return profile[["ncodpers", "month", "age", "sexo", "renta", "segmento"]]


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


def impute_and_encode(df: pd.DataFrame) -> pd.DataFrame:
    """Impute missing values with train-only statistics and one-hot encode
    the categorical fields, following the same train-only-fit /
    val-only-scored rule as Group 1 (docs/decisions/002-train-val-split.md).
    """
    df = df.copy()
    train_mask = df["split"] == "train"

    df["age_missing"] = df["age"].isna()
    age_median = df.loc[train_mask, "age"].median()
    df["age_years"] = df["age"].fillna(age_median).astype("float32")
    print(f"train-only age median used for imputation: {age_median:.1f}")

    # age's relationship with adoption is non-monotonic (rises, peaks in
    # middle age, falls - see docs/audit_log.md's
    # [correlation-yardstick-vs-nonmonotonic-feature] finding), which a
    # linear model can't capture from age_years alone. Centering on the
    # train-only mean before squaring (rather than squaring raw age) keeps
    # age_years and age_years_sq less correlated with each other, which
    # keeps logistic regression's coefficients on each term more stable.
    age_mean = df.loc[train_mask, "age_years"].mean()
    df["age_years_sq"] = ((df["age_years"] - age_mean) ** 2).astype("float32")
    print(f"train-only age mean used to center age_years_sq: {age_mean:.1f}")

    df["sexo_missing"] = df["sexo"].isna()
    df["sexo_h"] = (df["sexo"] == "H").astype("int8")
    df["sexo_v"] = (df["sexo"] == "V").astype("int8")

    df["segmento_missing"] = df["segmento"].isna()
    for code in ["top", "particulares", "universitario"]:
        df[f"segmento_{code}"] = (df["segmento"] == code).astype("int8")

    df["renta_missing"] = df["renta"].isna()
    global_median = df.loc[train_mask, "renta"].median()
    segment_medians = df.loc[train_mask].groupby("segmento", observed=True)["renta"].median()
    print(f"train-only global renta median: {global_median:,.0f}")
    print(f"train-only renta median by segmento:\n{segment_medians}")

    fallback = df["segmento"].map(segment_medians).fillna(global_median)
    df["renta_imputed"] = df["renta"].fillna(fallback).astype("float32")
    df["renta_log"] = np.log1p(df["renta_imputed"]).astype("float32")

    return df


def summarize(df: pd.DataFrame) -> None:
    for col in ["age_missing", "sexo_missing", "segmento_missing", "renta_missing"]:
        print(f"{col} rate: {df[col].mean():.3%}")
    print("\nmean feature value by split (sanity check, not leakage-sensitive):")
    print(df.groupby("split", observed=True)[["age_years", "renta_imputed", "renta_log"]].mean())


if __name__ == "__main__":
    split_df = load_split()
    profile = load_profile()

    merged = attach_profile(split_df, profile)
    del profile

    features = impute_and_encode(merged)
    summarize(features)

    out_cols = [
        "ncodpers", "fecha_dato", "split",
        "age_years", "age_years_sq", "age_missing",
        "sexo_h", "sexo_v", "sexo_missing",
        "segmento_top", "segmento_particulares", "segmento_universitario", "segmento_missing",
        "renta_imputed", "renta_log", "renta_missing",
    ]
    out = features[out_cols]
    out.to_parquet(OUTPUT_PATH, index=False)
    print(f"\nwrote {len(out)} rows to {OUTPUT_PATH}")

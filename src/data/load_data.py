"""Loader for the Santander Product Recommendation raw data.

Untested against the real file — data/raw/train_ver2.csv is not downloaded yet.
Once it is, run this module directly for a quick shape/missingness/memory report.
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
TRAIN_PATH = RAW_DIR / "train_ver2.csv"
TEST_PATH = RAW_DIR / "test_ver2.csv"


def load_train(nrows: int | None = None) -> pd.DataFrame:
    """Load train_ver2.csv, optionally limited to the first `nrows` rows for
    fast iteration during development."""
    return pd.read_csv(TRAIN_PATH, nrows=nrows, low_memory=False)


def load_test(nrows: int | None = None) -> pd.DataFrame:
    return pd.read_csv(TEST_PATH, nrows=nrows, low_memory=False)


def basic_report(df: pd.DataFrame, top_missing: int = 20) -> None:
    """Print shape, columns, top missing-value counts, and memory usage."""
    print(f"shape: {df.shape}")
    print(f"columns ({len(df.columns)}): {list(df.columns)}")

    missing = df.isna().sum().sort_values(ascending=False)
    missing = missing[missing > 0]
    print(f"\ntop {top_missing} columns by missing values:")
    print(missing.head(top_missing))

    mem_mb = df.memory_usage(deep=True).sum() / 1024**2
    print(f"\nmemory usage: {mem_mb:.1f} MB")


if __name__ == "__main__":
    df = load_train(nrows=100_000)
    basic_report(df)

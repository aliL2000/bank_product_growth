"""Loader for the Santander Product Recommendation raw data."""

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


def full_scan_report(path: Path = TRAIN_PATH, chunksize: int = 500_000) -> None:
    """Stream the full file in chunks to get exact row count and missingness
    without loading the whole file into memory at once. Prints a running
    total at the end."""
    total_rows = 0
    missing_total = None
    columns = None

    for chunk in pd.read_csv(path, chunksize=chunksize, low_memory=False):
        total_rows += len(chunk)
        if columns is None:
            columns = list(chunk.columns)
        chunk_missing = chunk.isna().sum()
        missing_total = chunk_missing if missing_total is None else missing_total + chunk_missing

    print(f"total rows: {total_rows}")
    print(f"columns ({len(columns)}): {columns}")
    missing_total = missing_total.sort_values(ascending=False)
    missing_total = missing_total[missing_total > 0]
    print(f"\nmissing values (full file, {total_rows} rows):")
    print(missing_total)
    print("\nmissing fraction:")
    print((missing_total / total_rows).round(4))


if __name__ == "__main__":
    df = load_train(nrows=100_000)
    basic_report(df)

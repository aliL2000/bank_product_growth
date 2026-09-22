"""Phase 3: identify an under-served, high-propensity customer segment.

"Under-served" = few existing products (`product_count_prev` 0-1) - the bank
hasn't captured much wallet share from these customers yet. "High-propensity"
= a real observed adoption rate meaningfully above other under-served
customers, not just a raw model score - per /audit finding
[uncalibrated-rare-leaf-scored-as-high-propensity] (docs/audit_log.md,
2026-09-21), individual LightGBM scores in the extreme tail are known to
overstate real propensity, so candidates are screened by *observed* group
rate instead.

Built on val, not test - exploratory segment discovery, not a reported
number, so it doesn't spend test's one-time-only guarantee
(docs/decisions/004-three-way-split.md).

Groups are a manual cross of the four features Phase 1-3 already identified
as the strongest signals: product_count_prev (tiered), segmento, activity_index,
and age_years (banded) - not a clustering algorithm, so every candidate
segment is directly interpretable as a business rule.

A group's raw observed rate is an unreliable point estimate when n is small
(the same root problem as the calibration audit finding, one level up: a
small group can show an extreme rate by chance). Candidates are ranked by
the Wilson score interval's *lower bound*, not the raw rate, so a group that
looks good only because it's small and got lucky doesn't outrank a
larger, more reliable one.
"""

from pathlib import Path

import numpy as np
import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"
MODELING_TABLE_PATH = PROCESSED_DIR / "modeling_table.parquet"

GROUP_COLS = ["product_tier", "segmento_label", "activity_label", "age_band"]

Z_95 = 1.959963985  # scipy.stats.norm.ppf(0.975)

MIN_GROUP_N = 5000  # ~20+ expected adopters at a ~0.4% base rate - small
# enough to find real segments, large enough that the Wilson lower bound
# is meaningful rather than just wide open.

AGE_BAND_EDGES = [0, 25, 35, 45, 55, 65, 200]
AGE_BAND_LABELS = ["<25", "25-34", "35-44", "45-54", "55-64", "65+"]


def load_val() -> pd.DataFrame:
    cols = [
        "product_count_prev",
        "activity_index",
        "age_years",
        "segmento_top",
        "segmento_particulares",
        "segmento_universitario",
        "segmento_missing",
        "adoption",
        "split",
    ]
    df = pd.read_parquet(MODELING_TABLE_PATH, columns=cols)
    return df[df["split"] == "val"].copy()


def label_segmento(df: pd.DataFrame) -> pd.Series:
    label = np.select(
        [
            df["segmento_top"] == 1,
            df["segmento_particulares"] == 1,
            df["segmento_universitario"] == 1,
        ],
        ["top", "particulares", "universitario"],
        default="missing",
    )
    return pd.Series(label, index=df.index)


def bucket_product_count(product_count_prev: pd.Series) -> pd.Series:
    return pd.cut(
        product_count_prev,
        bins=[-1, 0, 1, 100],
        labels=["0", "1", "2+"],
    )


def build_group_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["product_tier"] = bucket_product_count(df["product_count_prev"])
    df["segmento_label"] = label_segmento(df)
    df["activity_label"] = np.where(df["activity_index"] == 1, "active", "inactive")
    df["age_band"] = pd.cut(df["age_years"], bins=AGE_BAND_EDGES, labels=AGE_BAND_LABELS)
    return df


def wilson_lower_bound(x: np.ndarray, n: np.ndarray, z: float = Z_95) -> np.ndarray:
    """Lower bound of the Wilson score confidence interval for a binomial
    proportion - stays valid for rare-event rates where the normal
    (Wald) approximation breaks down."""
    phat = x / n
    denom = 1 + z**2 / n
    center = phat + z**2 / (2 * n)
    adj = z * np.sqrt(phat * (1 - phat) / n + z**2 / (4 * n**2))
    return (center - adj) / denom


def group_stats(df: pd.DataFrame, group_cols: list[str] = GROUP_COLS) -> pd.DataFrame:
    """Observed adoption rate, n, and a 95% Wilson lower bound per group."""
    g = df.groupby(group_cols, observed=True)["adoption"]
    stats = g.agg(n="size", adoptions="sum").reset_index()
    stats["observed_rate"] = stats["adoptions"] / stats["n"]
    stats["wilson_lower"] = wilson_lower_bound(stats["adoptions"].to_numpy(), stats["n"].to_numpy())
    return stats


def rank_underserved_segments(stats: pd.DataFrame, overall_rate: float, min_n: int = MIN_GROUP_N) -> pd.DataFrame:
    """Filter to under-served tiers (0 or 1 existing products) with enough
    volume to trust, then rank by lift *within the under-served population*
    (each tier's own baseline rate), not lift vs. the whole val population.

    product_count_prev is Phase 2's single strongest positive driver, so
    "few products" and "high overall-population propensity" pull in
    opposite directions by construction - almost no under-served group will
    beat the population-wide rate, and ranking against it would bury the
    real business question: among customers the bank hasn't sold much to
    yet, who converts relatively well? lift_vs_overall is kept alongside for
    context, but conservative_lift_vs_tier (ranked on the Wilson lower
    bound, not the raw rate, so a small lucky group can't win by chance) is
    the primary ranking.
    """
    candidates = stats[
        stats["product_tier"].isin(["0", "1"]) & (stats["n"] >= min_n)
    ].copy()

    tier_rate = (
        stats[stats["product_tier"].isin(["0", "1"])]
        .groupby("product_tier", observed=True)
        .apply(lambda g: g["adoptions"].sum() / g["n"].sum(), include_groups=False)
    )
    candidates["tier_rate"] = candidates["product_tier"].map(tier_rate)

    candidates["lift_vs_overall"] = candidates["observed_rate"] / overall_rate
    candidates["lift_vs_tier"] = candidates["observed_rate"] / candidates["tier_rate"]
    candidates["conservative_lift_vs_tier"] = candidates["wilson_lower"] / candidates["tier_rate"]
    return candidates.sort_values("conservative_lift_vs_tier", ascending=False)


def print_top_segments(ranked: pd.DataFrame, n: int = 10) -> None:
    display = ranked.head(n).copy()
    display["observed_rate"] = display["observed_rate"].map(lambda x: f"{x:.3%}")
    display["wilson_lower"] = display["wilson_lower"].map(lambda x: f"{x:.3%}")
    display["lift_vs_overall"] = display["lift_vs_overall"].map(lambda x: f"{x:.2f}x")
    display["lift_vs_tier"] = display["lift_vs_tier"].map(lambda x: f"{x:.2f}x")
    display["conservative_lift_vs_tier"] = display["conservative_lift_vs_tier"].map(lambda x: f"{x:.2f}x")
    print(display.to_string(index=False))


if __name__ == "__main__":
    val_df = load_val()
    val_df = build_group_columns(val_df)
    overall_rate = val_df["adoption"].mean()
    print(f"val overall adoption rate: {overall_rate:.3%} (n={len(val_df):,})")

    stats = group_stats(val_df)
    print(f"\n{len(stats)} groups total ({(stats['n'] >= MIN_GROUP_N).sum()} with n >= {MIN_GROUP_N:,})")

    ranked = rank_underserved_segments(stats, overall_rate)
    print(f"\ntop under-served, high-propensity candidates (n >= {MIN_GROUP_N:,}, ranked by Wilson lower bound):")
    print_top_segments(ranked)

    out_path = REPORTS_DIR / "segment_candidates.csv"
    ranked.to_csv(out_path, index=False)
    print(f"\nWrote {len(ranked)} candidates to {out_path}")

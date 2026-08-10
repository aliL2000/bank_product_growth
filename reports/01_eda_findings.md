# Phase 1 EDA: Credit Card Adoption — Findings

Source: `notebooks/01_eda.ipynb`. Descriptive only, no modeling. Purpose:
surface which customer attributes look worth engineering into Phase 2
features, using the adoption label built in
`src/features/build_adoption_label.py` (see
`docs/decisions/001-service-a-product-choice.md` for why credit card is the
target).

**Population**: 12,111,689 eligible customer-months (customers who did *not*
hold a credit card as of month *t-1*, and therefore could adopt in month *t*).
**Overall adoption rate**: 0.57%.

All segment breakdowns below join each eligible row to that customer's
*month t-1* profile (age, tenure, income, etc.) — not month *t* — to avoid
leakage from attributes that could themselves be a downstream consequence of
adopting the card. See the notebook's "Why we use month t-1 attributes"
section for the full reasoning.

## Over time

| Month | Eligible | Adoptions | Rate |
|---|---|---|---|
| 2015-02 | 587,315 | 3,471 | 0.591% |
| 2015-03 | 590,745 | 5,076 | 0.859% |
| 2015-04 | 591,796 | 4,627 | 0.782% |
| 2015-05 | 592,148 | 4,071 | 0.688% |
| 2015-06 | 592,856 | 4,655 | 0.785% |
| 2015-07 | 593,700 | 4,886 | 0.823% |
| 2015-08 | 791,202 | 4,379 | 0.554% |
| 2015-09 | 804,976 | 4,463 | 0.554% |
| 2015-10 | 827,442 | 4,461 | 0.539% |
| 2015-11 | 854,119 | 4,312 | 0.505% |
| 2015-12 | 868,027 | 4,295 | 0.495% |
| 2016-01 | 872,744 | 3,792 | 0.435% |
| 2016-02 | 878,996 | 3,881 | 0.442% |
| 2016-03 | 884,682 | 4,401 | 0.498% |
| 2016-04 | 889,085 | 4,100 | 0.461% |
| 2016-05 | 891,856 | 4,248 | 0.476% |

The rate roughly halved across the window: ~0.79–0.86% through mid-2015 down
to ~0.44–0.50% by early-mid 2016. No strong seasonal pattern beyond a small
bump each March. The eligible pool also grew steadily (~587k → ~892k) over
the same period — the base is shifting month to month, not just the rate, so
early- vs. late-window comparisons should account for that.

## By segment (month t-1 attributes)

| Segment | Adoption rate | Range |
|---|---|---|
| **Activity index** (active vs. inactive) | 1.28% vs. 0.03% | ~50x — largest effect found |
| **Segmento** (TOP / PARTICULARES / UNIVERSITARIO) | 3.01% / 0.75% / 0.09% | >30x |
| **Tenure** (<6 months → 20+ years) | 0.11% → 1.44% | ~13x, monotonic |
| **Income quintile** (bottom → top) | 0.36% → 0.88% | ~2.4x, monotonic |
| **Sex** (H vs. V) | 0.44% vs. 0.69% | ~1.6x |
| **Age** (peaks 40–50) | 0.01% (<20) → 1.1–1.2% (40–50) → 0.34% (70+) | non-monotonic, inverted U |
| **Channel** (top 15 by volume) | 1.4% (KAS) → 0.002% (KHQ) | wide spread, likely a proxy variable |

Full per-bucket numbers are in the notebook.

## Data-quality notes carried forward to Phase 2

- `antiguedad` (tenure) contains a `-999999` placeholder for some rows — a
  known bad-data pattern in this dataset. It fell out of this EDA's tenure
  buckets as an implicit NaN (bins started at -1), which was fine for a
  descriptive pass but needs **explicit** cleaning before Phase 2 feature
  engineering rather than a silent drop.
- `age` has implausible values up to 164 — same story: needs explicit
  capping/cleaning rather than relying on bins to silently exclude it.
- `renta` (income) is ~20% missing, consistent with the Phase 1 full-file
  missingness scan. Phase 2 will need an explicit imputation strategy (e.g.
  median by province or segment) rather than dropping ~1 in 5 rows.

## Implications for Phase 2 feature engineering

`ind_actividad_cliente` (activity), `antiguedad` (tenure), and `segmento`
show the strongest signal here and should be in the first feature set.
`renta` and `age` are real but comparatively weaker on their own — worth
keeping, not the headline story. `canal_entrada` is promising but
high-cardinality with many low-volume categories, so it likely needs
grouping into a smaller number of buckets rather than being used raw.

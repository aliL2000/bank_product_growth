# Phase 3: Explainability & Segmentation — Findings

Source: `src/models/explain_shap.py`, `src/models/check_calibration.py`,
`src/models/identify_segments.py`; walked through in
`notebooks/08_shap_explainability.ipynb`. Purpose: turn the LightGBM
baseline from a ranking tool into an explanation — what actually drives a
predicted adoption, whether its confidence can be trusted, and which real
customer segment the bank should prioritize for credit card outreach.

All findings below are computed on **val** (1,751,740 rows, 0.438% base
rate), not test — exploratory work, not a reported metric, so test's
one-time-only guarantee (`docs/decisions/004-three-way-split.md`) stays
unspent through all of Phase 3.

## What drives a prediction: SHAP on the LightGBM baseline

SHAP (Shapley) values decompose each customer's predicted score into an
exact, additive contribution from every feature — confirmed to reproduce
the raw score within 2.8e-13 across all 1,751,740 val rows. Ranked by mean
`|SHAP value|` (how much a feature moves a typical prediction, in either
direction):

| Feature | Mean \|SHAP\| | Direction |
|---|---|---|
| `activity_index` | 0.984 | Strongly positive — active customers push toward adoption |
| `age_years` | 0.622 | Positive on average, but non-monotonic (see below) |
| `product_count_prev` | 0.563 | Strongly positive — more existing products, more push toward adoption |
| `tenure_months` | 0.118 | Positive — longer relationship, more push toward adoption |
| `renta_log` (income) | 0.055 | Weak |
| everything else | ≤0.050 each | Segmento, sex, missing-value flags — individually minor |

**Plain English**: whether a customer is *currently active* with the bank
matters more to a specific prediction than any single static trait — more
than how many products they already hold, more than their age, more than
income. Product count and tenure are real, substantial contributors, but
secondary. Age's effect is real but shaped, not linear: the 2026-09-15
per-bin lift analysis found adoption peaks at 2.04x the overall rate around
ages 45–50 and falls off on both sides — a customer's age matters, but
"older is better" is the wrong takeaway.

## Reconciling three importance rankings that disagree

Three measures used across this project rank the top features differently,
and the disagreement itself is informative once unpacked:

| Feature | Raw correlation rank (Phase 2) | LightGBM split-count rank | SHAP mean\|value\| rank |
|---|---|---|---|
| `product_count_prev` | **1st** (r≈0.166) | 3rd (180 splits) | 3rd |
| `activity_index` | 2nd (r≈0.084) | 5th (56 splits) | **1st** |
| `tenure_months` | 3rd (r≈0.060) | 2nd (256 splits) | 4th |
| `age_years` | 4th (r≈0.036) | **1st** (292 splits) | 2nd |

Each measure answers a different question:
- **Raw correlation** asks "how strong is this feature's simple, roughly
  monotonic association with adoption, on its own?" `product_count_prev`
  wins because its relationship is close to a clean, straight climb — easy
  for a linear-style measure to detect.
- **Split count** asks "how many decision boundaries did the tree need to
  use this feature?" — a mechanical count, not an impact measure. `age_years`
  tops it *because* its relationship is complicated (rises, peaks, falls),
  so the tree needs many splits just to trace that one shape — a feature
  needing more splits isn't necessarily contributing more to any single
  prediction.
- **SHAP mean \|value\|** asks "how much does this feature actually move a
  typical prediction, accounting for everything else in the model?" — the
  only one of the three that's an exact, verified decomposition of the
  model's own output rather than a proxy. `activity_index` wins here: a
  single 0/1 flag, needing few splits, whose presence or absence still
  swings predictions more than any other feature on average.

**Which to trust**: SHAP is the most direct answer to "what actually drives
this model's predictions" — it's not a proxy for importance, it *is* each
prediction's decomposition, additivity-verified. Raw correlation and split
count are still useful context (correlation for "does this look linear,"
split count for "how complicated is this feature's shape"), but neither is
a substitute for SHAP when the three disagree.

## Guardrail: don't trust an individual score at face value

The 2026-09-21 `/audit` calibration check (`src/models/check_calibration.py`)
found LightGBM's predicted probabilities are **overconfident in the extreme
tail**: the top 0.01% of val (175 rows) predicts 43.2% on average against
an observed rate of only 3.4% — 12.6x overconfident — decaying fast to
1.47x by the top 0.1% and ~1.2x by the 1–5% range the formal precision@K
evaluation already validated. Group-level averages stay trustworthy; a
single row's near-certain score does not. This directly shaped how the
segment below was built: candidates are screened by each **group's**
observed adoption rate, never by an individual customer's raw predicted
score.

## The under-served, high-propensity segment

"Under-served" (few existing products) and "high-propensity" (likely to
adopt) pull in opposite directions by construction — `product_count_prev`
is the strongest positive driver in the table above, so fewer products
mechanically means lower propensity *relative to the whole population*.
Screening under-served customers against the population-wide rate found
nothing useful (every candidate scored below 1x). The real question is
different: **among customers with few products, who converts relatively
well?** — screening each candidate group against its own product-tier
baseline instead of the overall rate answered that cleanly.

**Segment**: customers who are currently **active**, in the **`particulares`**
customer segment, holding **exactly one existing product**, aged **35–64**.

| | |
|---|---|
| Val rows | 113,858 |
| Adoptions | 410 |
| Observed rate | 0.360% |
| One-product-tier baseline | 0.069% |
| Lift vs. tier baseline | **5.20x** (4.72x conservative — Wilson 95% lower bound) |

This isn't one lucky cell: the same three-way combination (one product,
`particulares`, active) ranked in the top 5 across every age band tested,
with a smooth decline in lift moving away from the strongest ages (55–64
highest, falling off toward both `<25` and `65+`) — a coherent pattern, not
scattered multiple-comparisons noise (`docs/concepts_log.md`, 2026-09-22
entry, has the full ranked table and the Wilson-interval reasoning).

**Caveats**:
- The `top` customer segment (highest baseline adoption rate historically)
  couldn't be evaluated here — only 8,567 val rows total hold 0-1 products
  across every age/activity combination, too few for any single cell to
  clear the reliability threshold. This finding says nothing about whether
  an under-served `top`-segment customer would convert even better; the
  data simply can't support checking.
- `product_count_prev` and `tenure_months` correlate moderately (r=0.269,
  `docs/audit_log.md` [unchecked-flagged-caveat]) — "exactly one product"
  and "35-64 years old" aren't fully independent signals; some of this
  segment's lift likely reflects tenure as well as product count.

## Business narrative (plain English)

The single most useful thing to know about a customer isn't a fixed trait
like age or income — it's whether they're **currently active** with the
bank. Beyond that, customers who already hold products and have stuck
around longer are meaningfully more likely to add another one; age matters
too, but the sweet spot is the mid-career years, not "older is always
better." The clearest opportunity for outreach isn't the average customer,
and it isn't the customer who looks best on a raw predicted score either
(the top of that ranking is not to be trusted at face value) — it's a
specific, sizeable, real group: **active, `particulares`-segment customers
who already hold exactly one product and are 35–64 years old**. They convert
to credit card holders at roughly **5x the rate of other single-product
customers**, and there are enough of them (114K in a single 2-month sample)
to be a genuine outreach target, not a statistical curiosity.

## Implications for Phase 4

- This segment is a ready-made **business-rule baseline** for Phase 4 —
  compare targeting by this simple rule against targeting by raw model
  score and against contacting everyone, under a simulated cost/value
  model.
- Worth checking whether the model's own predicted score already ranks
  this segment highly (in which case it's redundant with model-score
  targeting) or whether it's a distinct signal the model underweights (in
  which case combining the rule with the score could beat either alone) —
  an open question for Phase 4, not resolved here.
- `[eyeballed-cutoffs]` (age >100 cutoff, tenure buckets, income quintiles,
  and now this report's age bands) remains open and low-priority — none of
  today's findings depended on a cutoff being exactly right, just roughly
  reasonable.

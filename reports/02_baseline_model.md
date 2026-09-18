# Phase 2 Baseline Model: Credit Card Adoption — Findings

Source: `src/models/baseline_logistic_regression.py`,
`src/models/baseline_lightgbm.py`, `src/models/evaluate_precision_at_k.py`;
walked through in `notebooks/05_baseline_logistic_regression.ipynb`,
`notebooks/06_baseline_lightgbm.ipynb`, and
`notebooks/07_precision_at_k_evaluation.ipynb`. Purpose: establish a first
working model for credit card adoption, compare a linear baseline against
gradient boosted trees, and evaluate both the way the eventual targeting
decision will actually use them — a fixed contact budget, not an abstract
accuracy number.

**Population**: `data/processed/modeling_table.parquet`, 12,111,689 eligible
customer-months (non-holders at month *t-1*), 18 Phase 2 features (tenure,
activity index, product count, age + `age_years_sq`, income (log), sex,
segmento, plus a `*_missing` flag per imputed column).

**Split** (`docs/decisions/004-three-way-split.md`, time-respecting, no
random component):

| Split | Months | Rows | Adoptions | Rate |
|---|---|---|---|---|
| Train | 2015-02 – 2015-12 (11) | 7,694,326 | 48,696 | 0.633% |
| Val | 2016-01 – 2016-02 (2) | 1,751,740 | 7,673 | 0.438% |
| Test | 2016-03 – 2016-05 (3) | 2,665,623 | 12,749 | 0.478% |

Val is used only for model selection/early stopping. Test is scored exactly
once, below, for the numbers that matter.

## Models

| Model | Train ROC-AUC | Val ROC-AUC | Notes |
|---|---|---|---|
| Logistic regression | 0.906 | 0.912 | `class_weight="balanced"`, continuous features standardized on train-only stats. Needs `age_years_sq` (train-mean-centered) to fit age's non-monotonic peak — a plain linear term can't. |
| LightGBM | 0.9148 | 0.9198 | No scaling, no `age_years_sq` needed — tree splits are invariant to monotonic transforms and capture non-monotonic patterns natively. `is_unbalance=True` tried and rejected: it broke early stopping (`best_iteration_ == 1`) by destabilizing boosting's round-to-round val AUC, so the model is fit **without** class reweighting. `age_years` is the single most-split feature (292 of ~1,080 splits). |

Both models agree on the strongest signals: `age_years`, `tenure_months`,
`product_count_prev`, and `activity_index` dominate (matching Phase 1 EDA
and Phase 2's feature-check notebooks). Coefficient signs and split
importances are directionally consistent with each other and with the raw
EDA correlations.

## Formal evaluation: precision@K / recall@K vs. random targeting (test, scored once)

Precision@K: of the top-K customers contacted by predicted score, what
fraction actually adopt. Recall@K: of every adopter in test, what fraction
fall inside that top-K list. Lift@K: precision@K ÷ the overall test
adoption rate (0.478%) — how much better than random targeting the model's
ranking is. Random targeting's expected precision@K is just the base rate;
its expected recall@K is the contact fraction itself.

| Contact budget | Model | Contacted | Adopters captured | Precision | Recall | Lift |
|---|---|---|---|---|---|---|
| 0.1% | Logistic regression | 2,665 | 232 | 8.71% | 1.8% | 18.20x |
| 0.1% | LightGBM | 2,665 | 228 | 8.56% | 1.8% | 17.89x |
| 0.1% | Random | 2,665 | 13 | 0.48% | 0.1% | 1.00x |
| 0.5% | Logistic regression | 13,328 | 1,104 | 8.28% | 8.7% | 17.32x |
| 0.5% | LightGBM | 13,328 | 1,131 | 8.49% | 8.9% | 17.74x |
| 0.5% | Random | 13,328 | 64 | 0.48% | 0.5% | 1.00x |
| 1% | Logistic regression | 26,656 | 2,149 | 8.06% | 16.9% | 16.86x |
| 1% | LightGBM | 26,656 | 2,153 | 8.08% | 16.9% | 16.89x |
| 1% | Random | 26,656 | 127 | 0.48% | 1.0% | 1.00x |
| 2% | Logistic regression | 53,312 | 3,809 | 7.14% | 29.9% | 14.94x |
| 2% | LightGBM | 53,312 | 3,784 | 7.10% | 29.7% | 14.84x |
| 2% | Random | 53,312 | 255 | 0.48% | 2.0% | 1.00x |
| 5% | Logistic regression | 133,281 | 6,655 | 4.99% | 52.2% | 10.44x |
| 5% | LightGBM | 133,281 | 6,750 | 5.06% | 52.9% | 10.59x |
| 5% | Random | 133,281 | 637 | 0.48% | 5.0% | 1.00x |

Full table: `reports/baseline_precision_at_k.csv` (gitignored, regenerate
with `python -m models.evaluate_precision_at_k`).

**Read at a 1% contact budget**: calling the top 26,656 customers by score
reaches about 1 in 6 of all adopters in the whole test period, with roughly
1 in 12 calls landing on a real adopter — a ~17x improvement over calling
26,656 random customers, where only ~127 would adopt by chance.

**Precision decays and recall grows as the budget widens** — there's no
single "right" K without a real contact-capacity/cost constraint. That
constraint is exactly what Phase 4's targeting strategy and simulated ROI
work will supply; this table is the input to that decision, not the
decision itself.

## Key finding: the val-vs-test LightGBM edge shrinks to a tie

Both baseline sessions used val's top-1% lift as the headline comparison
number, where LightGBM looked clearly ahead of logistic regression (17.13x
vs. LR's 14–17x). Scoring test — the number that actually counts — tells a
different story: **the two models are essentially tied** at every budget
above, and LR is even slightly ahead at 0.1% and 2%. Val has only 7,673
adoption events vs. test's 12,749, so part of the earlier gap looks like
noise from the smaller validation sample rather than a robust LightGBM
advantage. Concretely (`notebooks/07_precision_at_k_evaluation.ipynb`):

| Model | Val lift@1% | Test lift@1% |
|---|---|---|
| Logistic regression | ~14–17x | 16.86x |
| LightGBM | 17.13x | 16.89x |

## Implications for Phase 3

- Neither model is a clear winner on the metric that will actually drive
  targeting decisions — LightGBM's added complexity (no interpretable
  coefficients, needs a fitted booster rather than a formula) isn't
  currently buying a real, robust lift advantage. Phase 3's SHAP work can
  be run on either model; LightGBM is still the more natural SHAP target
  (tree-based SHAP is exact and fast), but the near-tie means the
  precision@K table above — not just "which model is better" — is the
  right thing to carry into the business narrative.
- `age_years`/`age_years_sq` and `product_count_prev`/`tenure_months` are
  the standout signals in both models — Phase 3 should prioritize
  explaining *why* (e.g. does product count act as a proxy for existing
  bank relationship depth, or for something else) rather than treating
  them as a settled story.
- `canal_entrada` (deliberately deferred in Phase 2) is still not needed —
  neither model's evaluation surfaced a gap that points at missing channel
  information.

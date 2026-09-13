# Decision Record: Add a held-out test bucket (train/val/test)

## Title
Split into three chronological buckets instead of two — train (11 months),
val (2 months), test (3 months) — so val can be used for model selection
without contaminating the final reported number.

## Date
2026-09-13

## Context
Phase 2's next step is baseline logistic regression + LightGBM, comparing
them (and any hyperparameters) on val, then reporting a result in
`reports/02_baseline_model.md`. With only train/val, that reported number
would be optimistically biased — the same data used to pick the best
model/settings would also be used to claim how good it is. Flagged as
`/audit` finding [no-held-out-test-set] on 2026-09-11, left open at the time.

## Decision
- **Test = last 3 labeled months** (2016-03, 2016-04, 2016-05) — unchanged
  from the old val window. Touched once, at the very end, only to report the
  final baseline number.
- **Val = the 2 months before that** (2016-01, 2016-02) — used to compare
  LR vs. LightGBM and tune hyperparameters.
- **Train = every earlier labeled, eligible month** (2015-02 through
  2015-12, 11 months).
- `src/features/train_val_split.py` now writes a `split` column with three
  values (`train`/`val`/`test`) instead of two; `VAL_MONTHS` split into
  `TEST_MONTHS` (unchanged months) and a new, smaller `VAL_MONTHS`.

## Why
- **Keeping test = the old val window** preserves the exact deployment-like
  reasoning already settled in `docs/decisions/002-train-val-split.md`
  (most recent months, no gap month needed since the label is already
  point-in-time correct) for the number that will actually go in the report
  and `docs/resume_bullets.md` — no need to re-argue that reasoning.
- **2 months of val** (~1.75M rows, 7,673 adoption events) is enough to
  compare a handful of models/hyperparameter settings without being noise-
  dominated, while leaving 11 months (~7.69M rows, 48,696 events) for
  training — a smaller cut than val took from train originally (3 of 16
  months), since val's job here is comparison, not final reporting.
- **Chronological (not k-fold) split** — a rolling/expanding time-series
  cross-validation would be more statistically robust, but is
  disproportionate for a baseline LR + LightGBM comparison over 16 months
  total; revisit if Phase 3+ model selection gets more elaborate.

## Alternatives considered
- **Keep 2-way split, report val with a caveat**: rejected — leaves the
  audit finding open and produces a number that wouldn't hold up if
  scrutinized, which matters since this project's numbers are meant to
  eventually back resume bullets (`docs/resume_bullets.md`).
- **Time-series cross-validation** (multiple rolling windows): rejected for
  now as disproportionate complexity for a first baseline; the dataset only
  has 16 labeled months to begin with.
- **1-month val instead of 2**: considered, to keep more data in train;
  not chosen because 2 months roughly doubles val's adoption-event count
  over 1 month, meaningfully firming up model-selection comparisons at
  small cost to train size (11 vs. 12 months).

## Consequences / what this affects downstream
- `data/processed/train_val_split.parquet` regenerated: train 7,694,326
  rows / 48,696 adoptions (0.633%), val 1,751,740 rows / 7,673 adoptions
  (0.438%), test 2,665,623 rows / 12,749 adoptions (0.478%) — test's counts
  are unchanged from the old val bucket, as expected.
- All three Phase 2 feature files (`features_tenure_activity`,
  `features_product_count`, `features_demographics`) rebuilt against the
  corrected split; any train-only imputation statistics inside them
  (tenure median, activity mode, age median, renta median-by-segmento)
  shifted slightly since train now excludes 2016-01/02, but feature ranking
  and correlation magnitudes were re-verified essentially unchanged
  (notebooks 02–04 re-executed: tenure 0.059→0.060, activity 0.083→0.084,
  product_count_prev 0.163→0.166, age 0.035→0.036).
- `tests/test_train_val_split.py` updated for the new three-way boundary.
- Baseline modeling (next roadmap step) trains on `train`, selects between
  LR/LightGBM and tunes on `val`, and reports the final number on `test`
  exactly once.

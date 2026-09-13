# Audit Log

Dated entries from `/audit` runs (see `.claude/skills/audit/SKILL.md`) — a
critical review of methodology, code, and process. Each finding has a short
id so later audits can reference it as RESOLVED / STILL OPEN / PARTIALLY
ADDRESSED instead of re-explaining it from scratch.

### 2026-09-11 (first audit, given informally before the skill existed)

**Strengths**: point-in-time (t-1) joins done correctly and consistently
across all three feature groups; train-only imputation statistics honored
throughout; time-based split reasoning is sound; decisions are logged
instead of left implicit.

**Findings** (all OPEN):

1. **[contaminated-negative-class]** `train_val_split.csv` keeps every
   labeled row, including customers who already held a credit card at t-1
   (`adoption` trivially `False` for them, not a real "chose not to adopt").
   Phase 1's eligible-non-holder count was 12,111,689 vs. the split's
   12,682,421 rows — a ~570,732-row (4.5%) gap of already-holders sitting in
   the negative class. Fix: filter to `prev_flag == 0` before building the
   split, or explicitly justify keeping them.
2. **[no-baseline-model-yet]** Three feature-engineering sessions completed
   before training a single model. Feature value so far is inferred purely
   from univariate correlation with the label, which doesn't guarantee
   multivariate usefulness (Groups 1-2 may be redundant with each other).
   Standard practice is an ugly end-to-end baseline first, then invest in
   features once the pipeline's real output is known.
3. **[no-held-out-test-set]** Only train/val exists. Once val is used for
   both model selection (LR vs. LightGBM, hyperparameters) and the reported
   number in `reports/02_baseline_model.md`, that number is optimistically
   biased. Needs a third held-out split (or a held-out final month).
4. **[no-tests-on-label-logic]** The adoption-label construction is the
   single point of failure for the whole project and has no unit test (e.g.
   a synthetic small dataset asserting expected labels) and no merge-safety
   assertions (e.g. row count unchanged after a left join) anywhere in the
   three feature-build scripts.
5. **[csv-intermediate-files]** Multiple ~600MB+ gitignored CSVs for
   intermediate features at 12.68M rows. Parquet would be smaller, faster,
   and preserve dtypes, removing the need to re-declare `dtype=` dicts by
   hand in every downstream script (already a source of one real pandas bug
   on 2026-08-13).
6. **[env-reproducibility]** On 2026-08-10, `requirements.txt` was
   discovered not to be fully installed despite being the documented
   environment spec. No CI or check catches this automatically; it was
   noticed by accident.
7. **[eyeballed-cutoffs]** Several bin edges (age >100 cutoff, tenure
   buckets, income quintiles) are chosen by eye rather than derived
   (e.g. decision-tree splits, WOE binning). Defensible at EDA stage, less
   so if this needs to hold up under scrutiny later.
8. **[docs-outpacing-modeling]** ROADMAP working log, concepts log,
   decisions folder, resume-bullets doc, and two generated PDFs all exist
   before any model has been trained. Reasonable at week 5 of 16; worth
   checking the ratio doesn't stay this way by week 16.

### 2026-09-11 (first run via the `/audit` skill)

**Strengths**: point-in-time merge joins verified correct in practice —
confirmed `(ncodpers, fecha_dato)` is actually unique in `train_ver2.csv`
(label output row count matches raw row count exactly: 13,647,309), so no
silent merge-row-duplication is currently occurring despite no assertion
enforcing it; train-only imputation statistics correctly isolated
everywhere including the newer group-wise `renta` median; `segmento`
one-hot mapping covers 100% of non-null raw category values.

**New findings**:

1. **[stale-correlation-numbers-already-contaminated]** Checked whether
   `notebooks/02-04_feature_check_group*.ipynb` filter out already-holder
   rows before computing feature-adoption correlations — they don't (each
   does `train = merged[merged.split == 'train']` with no `prev_flag == 0`
   filter). This means the headline numbers already written into
   `ROADMAP.md` (e.g. product_count_prev's ~0.13 correlation, "strongest
   signal found so far") are computed over a train split where 4.5%
   (570,732 rows, recomputed and confirmed) are already-holders whose
   `adoption` is trivially `False` for a reason unrelated to propensity.
   This is the same root cause as [contaminated-negative-class] (still
   open below) but a newly-confirmed *consequence*: it's already biasing
   numbers used to judge feature strength, not just a future train.csv
   risk. Fix: re-run the three feature-check notebooks with a
   `prev_flag == 0` filter (or fix it once upstream in the split) before
   those correlation numbers drive baseline feature choices.
2. **[correlation-yardstick-vs-nonmonotonic-feature]** `age_years`
   (correlation 0.0327 in `notebooks/04_feature_check_group3.ipynb`) is
   being compared on the same linear-correlation scale as monotonic
   features (tenure ~0.05, product_count ~0.13) despite Phase 1 EDA and
   this same notebook noting age's relationship is non-monotonic (peaks in
   middle age). Point-biserial/Pearson correlation is the wrong tool to
   rank a non-monotonic feature's "strength" against monotonic ones on the
   same axis. Fix: use a rank-correlation or per-bin lift table for age
   instead of/alongside linear correlation.

**Carried over from 2026-09-11 (informal, pre-skill) audit** — all 8
re-checked against current code and data, not memory:

1. **[contaminated-negative-class] — STILL OPEN**, numbers re-confirmed
   exactly (12,682,421 total / 12,111,689 eligible / 570,732
   already-holders, 4.50%). Now also shown to be contaminating the
   feature-check correlation numbers themselves (see new finding #1).
2. **[no-baseline-model-yet] — STILL OPEN.** Four sessions deep (split + 3
   feature groups), zero models trained. 6.4 of 16 project-weeks elapsed;
   Phase 2's own weeks 5-7 window is nearly spent with baseline not
   started.
3. **[no-held-out-test-set] — STILL OPEN.** No third split exists.
4. **[no-tests-on-label-logic] — STILL OPEN.** Zero `assert` statements
   anywhere in `src/` (grepped), zero test files in the repo. Live risk:
   the next roadmap step (assembling train.csv/val.csv via a 4-way join)
   has nothing to catch a row-count mismatch.
5. **[csv-intermediate-files] — STILL OPEN**, larger: `data/processed/`
   now ~2.9 GB across 5 CSVs (was 3 at last audit).
6. **[env-reproducibility] — STILL OPEN.** `requirements.txt` still
   unpinned; confirmed no lockfile, no CI config anywhere in the repo.
7. **[eyeballed-cutoffs] — STILL OPEN, partially mitigated.** New
   `age > 100` cutoff (Group 3) has documented domain reasoning (Spain's
   junior accounts) but is still not data-derived.
8. **[docs-outpacing-modeling] — STILL OPEN, worsening.** `concepts_log.md`
   grew from 5 to 10 entries this session alone; `docs/audit_log.md` is
   itself a new recurring doc. Zero lines of modeling code exist.

**Bottom line**: engineering hygiene on what's been built is solid, but
the project is 6+ weeks and four sessions into Phase 2 with no model
trained, and the one number currently being used to judge which features
matter (product_count's ~0.13 correlation) is itself computed on a
provably contaminated train slice — that combination is the priority risk
right now, ahead of any single carried-over item.

### 2026-09-12 — status update (no new /audit run; fixes made in a normal session)

1. **[contaminated-negative-class] — RESOLVED**, as of the 2026-09-11
   "cont'd 2" session (this update was just late to be logged here):
   `train_val_split.py` now filters to `label_defined & (prev_flag == 0)`
   before assigning train/val. See `docs/decisions/003-eligibility-filter.md`.
2. **[stale-correlation-numbers-already-contaminated] — RESOLVED** as a
   direct consequence of #1: all three feature files and their sanity-check
   notebooks were rebuilt against the corrected split.
3. **[csv-intermediate-files] — RESOLVED.** All five `data/processed/`
   intermediates migrated from CSV to Parquet (`adoption_labels_tjcr`,
   `train_val_split`, and the three `features_*` files). `data/processed/`
   dropped from ~2.9 GB to ~395 MB (~7x). All five build scripts and all
   four notebooks (`01_eda` through `04_feature_check_group3`) updated to
   read/write Parquet and re-executed to confirm identical results (e.g.
   `product_count_prev`'s correlation reproduced exactly: 0.163054 before
   and after). New concept logged in `docs/concepts_log.md`.
4. **[no-tests-on-label-logic] — PARTIALLY ADDRESSED.** Added `pytest` +
   `tests/` (12 tests) covering `build_label()`'s core scenarios and each
   feature script's t-1 join, plus a runtime `assert len(merged) ==
   len(input)` in `build_label()` and each `attach_profile()` right after
   the merge. Not addressed: no CI wiring to run these automatically (still
   manual, via VSCode's Test Explorer or `pytest` in a terminal) - see
   [env-reproducibility] below, which is the more general version of that
   gap.

**Still open, unchanged**: [no-baseline-model-yet], [no-held-out-test-set],
[env-reproducibility], [eyeballed-cutoffs] (partially mitigated),
[docs-outpacing-modeling], [correlation-yardstick-vs-nonmonotonic-feature].

### 2026-09-13 — status update (no new /audit run; fix made in a normal session)

1. **[no-held-out-test-set] — RESOLVED.** `train_val_split.py` now assigns
   a three-way `train`/`val`/`test` split instead of two: train = 2015-02
   to 2015-12 (11 months), val = 2016-01 to 2016-02 (2 months, for model
   selection), test = 2016-03 to 2016-05 (3 months, unchanged from the old
   val window — held out, reported once). See
   `docs/decisions/004-three-way-split.md`. All three Phase 2 feature files
   and their sanity-check notebooks rebuilt/re-run against the corrected
   split; feature ranking and correlation magnitudes essentially unchanged
   (product_count_prev 0.163→0.166, tenure 0.059→0.060, activity
   0.083→0.084, age 0.035→0.036). `tests/test_train_val_split.py` updated
   for the new boundary; all 13 tests pass.

**Still open, unchanged**: [no-baseline-model-yet], [env-reproducibility],
[eyeballed-cutoffs] (partially mitigated), [docs-outpacing-modeling],
[correlation-yardstick-vs-nonmonotonic-feature].

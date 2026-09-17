# Roadmap

5 phases, ~16 weeks. This is a living document — update checkboxes and add a dated
entry to the working log every session, even a short one.

> **Status at a glance (update this block every session — keep it to ~5 lines):**
> **Phase 1 is complete.** Service A is decided (credit card,
> `ind_tjcr_fin_ult1`; see `docs/decisions/001-service-a-product-choice.md`),
> the adoption label is built (`data/processed/adoption_labels_tjcr.parquet`,
> gitignored — rerun `src/features/build_adoption_label.py` if missing), and
> the EDA notebook + findings write-up are done (`notebooks/01_eda.ipynb`,
> `reports/01_eda_findings.md`) — strongest signals found: activity index,
> tenure, segmento.
> **Time-respecting train/val split is done** (`data/processed/train_val_split.parquet`,
> gitignored — rerun `src/features/train_val_split.py` if missing; last 3
> labeled months as val, see `docs/decisions/002-train-val-split.md`).
> **Phase 2 feature engineering: Groups 1-3 done** — tenure/activity, product
> count (strongest signal, ~0.163 correlation), and demographics
> (age/sex/segmento/income) are all built and sanity-checked.
> `canal_entrada` (162-category channel column) is deliberately deferred,
> not built — revisit only if baseline model evaluation suggests it's
> needed. **Modeling population is now restricted to eligible non-holders**
> (`prev_flag == 0`) — split and all three feature files were rebuilt after
> `/audit` found already-holders contaminating the negative class (see
> `docs/decisions/003-eligibility-filter.md`). **All `data/processed/`
> intermediates are now Parquet** (~7x smaller than the old CSVs), and a
> `tests/` suite (13 pytest tests, runnable from VSCode's Test Explorer)
> covers the label-merge and feature-join logic. **Split is now 3-way**
> (train 11 months / val 2 months / test 3 months, see
> `docs/decisions/004-three-way-split.md`) so val can be used for model
> selection without biasing the final reported number. **Environment is
> installed and pinned** (`requirements.txt`, all versions confirmed
> working together — `pip install -r requirements.txt` is sufficient).
> **Modeling table is assembled** (`data/processed/modeling_table.parquet`,
> gitignored — rerun `src/features/build_modeling_table.py` if missing):
> 12,111,689 rows x 23 columns, one row per eligible labeled customer-month
> with `split`, `adoption` (target), and all Phase 2 features. **Age's
> correlation was re-checked with a per-bin lift table** (not just Pearson)
> per `/audit`'s [correlation-yardstick-vs-nonmonotonic-feature] finding —
> confirmed a real, strong non-monotonic pattern (peaks 45-50 at 2.04x the
> overall rate), so `age_years_sq` (train-mean-centered) was added to
> `build_features_demographics.py` so logistic regression can fit it too.
> **Baseline logistic regression is done** (`src/models/baseline_logistic_regression.py`,
> fit on train, quick sanity check on val): ROC-AUC 0.906 train / 0.912 val,
> ~14-17x lift in the top 1% of scored customers, coefficients directionally
> consistent with EDA. **Next up:** LightGBM (same train/val split), then
> the formal precision@K evaluation vs. random targeting comparing both
> models, reported once on test. Full detail is in the Working Log below.

## Phase 0 — Setup (Week 1)
- [x] Scaffold repo structure
- [x] Write `.gitignore`, `requirements.txt`
- [x] Draft `README.md`, `docs/dataset.md`, `docs/problem_statement.md`
- [x] Write `src/data/load_data.py` loader skeleton
- [x] Download `train_ver2.csv` / `test_ver2.csv` into `data/raw/`
- [ ] Set up GitHub remote and push

## Phase 1 — Understand the Data (Weeks 2–4)
- [x] Run `load_data.py` against real data, check shape/dtypes/memory footprint
- [x] Profile missingness across all 24 profile columns (full-file scan)
- [x] Finalize which product is "Service A" (log decision in `docs/decisions/`)
- [x] Build the adoption label (lacked product in month t-1, gained it in month t)
- [x] First EDA notebook — adoption rate over time, by segment
- [x] Write `reports/01_eda_findings.md`

## Phase 2 — Baseline Model (Weeks 5–7)
- [x] Time-respecting train/val split (train on earlier months, validate on later)
- [x] Feature engineering: tenure, activity index, product count, demographics
      (channel/`canal_entrada` deliberately deferred — see status block)
- [ ] Baseline logistic regression (done) + LightGBM (not started)
- [ ] Evaluate with precision@K / lift over random targeting baseline
- [ ] Write `reports/02_baseline_model.md`

## Phase 3 — Explainability & Segmentation (Weeks 8–10)
- [ ] SHAP values on best model
- [ ] Translate top drivers into plain-English business narrative
- [ ] Identify an under-served, high-propensity customer segment
- [ ] Write `reports/03_explainability_segments.md`

## Phase 4 — Targeting Strategy & Simulated ROI (Weeks 11–13)
- [ ] Define cost-per-contact and value-per-adoption assumptions (explicitly labeled
      as simulated, not real bank economics)
- [ ] Compare: model-score targeting vs. simple business rule vs. contact-everyone
- [ ] Write `reports/04_targeting_roi.md`

## Phase 5 — Polish (Weeks 14–16)
- [ ] Lightweight Streamlit dashboard
- [ ] Executive summary (1-pager)
- [ ] Interview cheat sheet — anticipated questions and answers

---

## Working Log

### 2026-07-28
- Initialized git repo, created folder structure, `.gitignore`, `requirements.txt`.
- Drafted `README.md`, `docs/dataset.md`, `docs/problem_statement.md`,
  `docs/decisions/000-template.md`.
- Wrote `src/data/load_data.py` loader skeleton (untested against real data — no
  data downloaded yet).
- Next: download `train_ver2.csv`/`test_ver2.csv` from Kaggle into `data/raw/`,
  then start Phase 1.

### 2026-07-28 (cont'd)
- Data downloaded: `train_ver2.csv` (2.29 GB, 13,647,309 rows), `test_ver2.csv`
  (110 MB, 929,616 rows) confirmed in `data/raw/`. Row/column counts match the
  expected dataset size (48 columns = 24 profile + 24 product flags).
- A naive full `pd.read_csv` would land around ~15 GB in memory (extrapolated from
  a 100k-row sample at 110.6 MB) — too close to this machine's headroom to load
  carelessly, so added `full_scan_report()` to `load_data.py`, which streams the
  file in 500k-row chunks to get exact row counts and missingness without holding
  the whole file in RAM. Ran it against the full train file.
- Missingness findings (full file, 13,647,309 rows): `conyuemp` and
  `ult_fec_cli_1t` are ~99.8–100% missing (near-useless, likely drop); `renta`
  (income) is ~20.5% missing (needs an imputation strategy — probably important
  given `renta` is likely a key adoption driver); `segmento`, `canal_entrada`,
  `indrel_1mes`/`tiprel_1mes` in the 1–1.4% range; a cluster of profile columns
  (`sexo`, `indfall`, `indext`, `ind_actividad_cliente`, etc.) all missing at
  exactly the same ~0.20% rate, suggesting a shared set of rows with a data
  quality issue worth investigating together rather than column-by-column.
- Not yet done: dtype optimization for a full in-memory load, Service A decision,
  adoption label construction, EDA notebook, `reports/01_eda_findings.md`.
- Next: decide on memory-safe full-load strategy (dtype downcasting / chunked
  feature engineering), then finalize Service A and build the adoption label.

### 2026-07-29
- Finalized Service A = credit card (`ind_tjcr_fin_ult1`). Computed month-by-month
  prevalence via a chunked scan (grouped by `fecha_dato`, summed the flag) across
  all 17 months: ranges from ~5.8% (mid-2015) down to ~3.7% (mid-2016) of
  customers holding a card — a large non-holder pool, and a product a bank can
  plausibly influence with outreach, unlike payroll (employer-switch-driven).
  Logged full reasoning in `docs/decisions/001-service-a-product-choice.md`,
  updated `docs/dataset.md` and `README.md` to reflect the decision as settled.
- Repo pushed to GitHub: https://github.com/aliL2000/bank_product_growth
  (remote added by Claude; push run by Adam per the no-push-credentials boundary).
- Next: build the adoption label (non-holder in month t-1, holder in month t)
  and start the first EDA notebook.

### 2026-08-02
- Built the credit card adoption label in `src/features/build_adoption_label.py`.
  Loaded only the 3 needed columns (`fecha_dato`, `ncodpers`, `ind_tjcr_fin_ult1`)
  with narrow dtypes (int32/int8) — 273 MB in memory, no chunking needed, since
  the earlier ~15 GB memory concern was specific to loading all 48 columns.
- Used a merge-based lag join (each row matched to the same customer's row at
  month-1 via an explicit `(ncodpers, month)` key) instead of a positional
  `groupby().shift()`, since 7.1% of rows (964,888) have no prior-month row at
  all (new customers / gaps) and a positional shift would have silently mislabeled
  those. Both techniques logged in `docs/concepts_log.md`.
- Key finding: adoption rate is **~0.57% per month** among eligible non-holders
  (69,118 adoption events out of 12,111,689 eligible customer-months) — a rare
  event. This is a real class-imbalance problem and will shape Phase 2 model
  choices (e.g. can't just optimize accuracy; may need class weighting or
  threshold/ranking-based evaluation, which fits the precision@K framing anyway).
- Output written to `data/processed/adoption_labels_tjcr.csv` (599 MB, gitignored,
  not committed).
- Next: first EDA notebook — adoption rate over time and by customer segment,
  then `reports/01_eda_findings.md`.

### 2026-08-10
- Refreshed `reports/Project_Recap.pdf` (a plain-language, non-ML-audience
  project summary) via a new reusable generator script,
  `src/reports/generate_project_recap.py` (uses `fpdf2`, added to
  `requirements.txt`). No content changes this pass — the recap already
  matched the 2026-08-02 state — but it's now a one-command rebuild instead
  of a one-off artifact.
- Built `notebooks/01_eda.ipynb`: adoption rate over time (roughly halved
  across the 17-month window, ~0.79–0.86% in mid-2015 down to ~0.44–0.50% by
  early-mid 2016, no strong seasonality) and by customer segment. Segment
  breakdowns join each labeled row to that customer's **month t-1** profile
  attributes (not month t) specifically to avoid label leakage — logged as a
  new concept in `docs/concepts_log.md` (point-in-time correctness).
- Strongest signals found: `ind_actividad_cliente` (activity index: 1.28% vs.
  0.03%, ~50x), `segmento` (TOP 3.01% vs. UNIVERSITARIO 0.09%, >30x), and
  `antiguedad`/tenure (0.11% → 1.44% monotonically with tenure, ~13x).
  Weaker but real: income (~2.4x top vs. bottom quintile), sex (~1.6x), age
  (non-monotonic, peaks at 40–50). Full numbers and data-quality caveats
  (`antiguedad`'s `-999999` placeholder, implausible `age` values up to 164,
  `renta`'s ~20% missingness) written up in `reports/01_eda_findings.md`.
- Discovered `requirements.txt` wasn't actually fully installed in this
  environment (only pandas/numpy were present) — installed `matplotlib`,
  `nbconvert`, and `ipykernel` as needed to run the notebook.
- **Phase 1 is now complete.**
- Next: Phase 2 — time-respecting train/val split (train on earlier months,
  validate on later), then feature engineering building on today's findings
  (activity index, tenure, segmento as priority features; explicit cleaning
  needed for `antiguedad`'s placeholder value and `age`'s outliers; an
  imputation strategy for `renta`).

### 2026-08-11
- No code changes. Adam wants this project to eventually be a resume bullet
  section, modeled on an existing 4-bullet project entry from one of his
  resumes. Drafted a phase-mapped version in `docs/resume_bullets.md` (new
  living doc, same pattern as `concepts_log.md`) — bullet 1 unlocks at Phase
  2, full 4-bullet section at Phase 4. Bullets stay `draft` until the phase
  that makes them true is actually done; numbers get filled from real results
  at that point, not estimated ahead of time.
- Next: continue with Phase 2 (time-respecting split, feature engineering) as
  previously planned. Revisit `docs/resume_bullets.md` when Phase 2 closes
  out to flip bullet 1 to `verified`.

### 2026-08-13
- Built the time-respecting train/val split: `src/features/train_val_split.py`
  reads `adoption_labels_tjcr.csv`, keeps only rows with a defined label (16
  months, 2015-02 through 2016-05), and tags the last 3 labeled months
  (2016-03/04/05) as `val`, the other 13 as `train` — no random component,
  no gap month (each row is already point-in-time correct via the Phase 1
  t-1 join). Full reasoning, including why this is a period split rather
  than a customer-holdout split, in `docs/decisions/002-train-val-split.md`;
  concept logged in `docs/concepts_log.md`.
- Result: train = 9,913,274 rows / 56,369 adoptions (0.57%); val = 2,769,147
  rows / 12,749 adoptions (0.46%). Output written to
  `data/processed/train_val_split.csv` (gitignored, rerun the script if
  missing).
- Note: hit a recurring pandas `IndexError` in `_concatenate_chunks` when
  reading `adoption_labels_tjcr.csv` without explicit `dtype=` on every
  `usecols` column (including the boolean-as-string `adoption`/`label_defined`
  columns) — fixed by declaring dtypes for all loaded columns rather than
  letting pandas infer them. Worth remembering if this file is read again
  without full dtypes specified.
- Next: Phase 2 feature engineering — tenure, product count, channel
  activity, demographics — joined against `train_val_split.csv`, built from
  train-only statistics where any aggregation is involved (per the caveat in
  `docs/decisions/002-train-val-split.md`).

### 2026-08-17
- Built the first Phase 2 feature group — tenure and activity index — in
  `src/features/build_features_tenure_activity.py`. Joins
  `train_val_split.csv` to each customer's `antiguedad`/`ind_actividad_cliente`
  at month *t-1* (same merge-key trick as the label build/EDA), cleans the
  `antiguedad` `-999999` placeholder and string `"NA"` flagged in
  `reports/01_eda_findings.md`, and imputes missing values (0.161% of rows)
  using train-only median/mode plus an explicit `*_missing` flag — new
  concept logged in `docs/concepts_log.md`.
- Match rate to a t-1 profile row was 100% (expected — same source table as
  the label build, so any row with a defined label already has a matching
  profile row). Output: `data/processed/features_tenure_activity.csv`
  (12,682,421 rows, gitignored).
- Sanity-checked the engineered features against the adoption label in a new
  notebook, `notebooks/02_feature_check_group1.ipynb` (train split only):
  both `activity_index` (0.03% inactive vs. 1.18% active) and `tenure_months`
  buckets (0.11% → 1.27%, monotonic) reproduce the same signal the Phase 1
  EDA found on the raw columns, confirming cleaning/imputation didn't wash
  it out. Notable side-finding: the 0.16% of rows that got an imputed value
  adopt at 0.054% vs. 0.570% for normal rows — real and meaningfully lower,
  which validates keeping `tenure_missing`/`activity_missing` as their own
  features rather than just filling and moving on.
- Refreshed both `reports/Project_Recap.pdf` and `reports/Technical_Deep_Dive.pdf`
  (via their generator scripts) to cover the train/val split and this first
  feature group, so the audience-facing docs aren't stuck at the Phase 1
  snapshot.
- Next: Group 2 — product count (how many of the 24 product flags a customer
  already holds at t-1), following the same script pattern.

### 2026-09-11
- Built the second Phase 2 feature group — product count — in
  `src/features/build_features_product_count.py`, following Group 1's
  pattern: joins `train_val_split.csv` to each customer's product flags at
  month *t-1* and sums 23 of the 24 `ind_*_ult1` flags into
  `product_count_prev`. Deliberately excludes the target column
  (`ind_tjcr_fin_ult1`) from the sum, since eligibility already forces it to
  0 for the rows that matter — including it would just re-encode the label
  rather than add signal. New concept (aggregating many raw columns into
  one derived feature) logged in `docs/concepts_log.md`.
- Found and handled a real data quirk: `ind_nomina_ult1`/`ind_nom_pens_ult1`
  (payroll, payroll pension) are missing for 16,063 rows each (0.12%) —
  filled with 0 rather than adding a per-column missing flag, since the
  effect on a 23-column sum is negligible. Match rate to a t-1 profile row
  was 100%, same as Group 1.
- Sanity-checked in a new notebook, `notebooks/03_feature_check_group2.ipynb`
  (train split only): **product_count_prev is the strongest signal found so
  far in this project** — adoption rate climbs from ~0.07% (0 other
  products) to ~4.3% (6+ products), a ~60x lift, with a point-biserial
  correlation (~0.13) noticeably higher than Group 1's tenure (~0.05) or
  activity index (~0.08). Flagged a caveat to revisit in Phase 3: product
  count likely correlates with tenure (both accumulate over time), so their
  individual lifts aren't necessarily additive once combined in a model.
- Next: Group 3 — demographics (income, age, sex, segmento), including a
  decision on the `renta` imputation strategy (~20% missing) and cleaning
  the implausible `age` outliers (>100) found in Phase 1 EDA.

### 2026-09-11 (cont'd)
- Built Group 3 — demographics — in `src/features/build_features_demographics.py`.
  Explored raw distributions first (age, sexo, segmento, renta) to make
  informed cleaning decisions rather than defaulting to Group 1's pattern:
  - `age`: only values >100 (12,869 rows, clearly implausible — raw max was
    164) become NaN + train-only median imputed; ages <15 left alone since
    Spain's custodial "junior" accounts make young holders real data.
  - `sexo`/`segmento`: one-hot encoded + `*_missing` flags.
  - `renta` (income, ~20% missing): imputed with a **train-only median
    grouped by segmento** (€89k-142k range across segments) rather than one
    flat global median — a step up from Group 1's plain global-median
    approach, with a global-median fallback for the ~1.4% of rows where
    segmento itself is missing. Also added `renta_log` (log1p transform)
    since raw income is heavily right-skewed (mean ~€135k vs. median
    ~€102k, max ~€29M) — needed for the upcoming logistic regression
    baseline. Both new concepts (group-wise imputation, log-transforming a
    skewed feature) logged in `docs/concepts_log.md`.
- Sanity-checked in `notebooks/04_feature_check_group3.ipynb` (train split
  only): all four features reproduce their Phase 1 raw-column findings —
  segmento remains the strongest of the group (top 2.43% vs. universitario
  0.097%, ~25x, close to Phase 1's >30x), age peaks in middle age, sex shows
  the expected small gap. Confirmed the log-transform empirically:
  `renta_log`'s correlation with adoption (~0.022) is 2.6x
  `renta_imputed`'s (~0.008). None individually rival Group 2's product
  count (~0.13) — demographics are real but comparatively weak predictors,
  consistent with Phase 1's "weaker but real" framing. Output:
  `data/processed/features_demographics.csv` (12,682,421 rows, gitignored).
- Decided: `canal_entrada` (channel of entry, 162 categories) is
  deliberately deferred rather than built as a Group 4 — the standard ML
  workflow is baseline-first, then decide what's worth adding based on
  evaluation results, not perfect the feature set before ever training a
  model. Revisit only if precision@K or feature importance later suggests
  it's needed. **Phase 2 feature engineering is done** (Groups 1-3).
- Next: assemble `train_val_split.csv` + all three feature-group files +
  the label into a single `train.csv`/`val.csv`, then baseline logistic
  regression + LightGBM, evaluated with precision@K vs. random targeting.

### 2026-09-11 (cont'd 2) — /audit fix: eligibility filter

- Ran `/audit` for the first time via the new skill. Top finding: the
  train/val split kept 570,732 rows (4.5%) where the customer already held
  a credit card at t-1 — their `adoption` is trivially `False`, not a real
  "chose not to adopt," and the three feature-check notebooks' correlation
  numbers (including the "strongest signal so far" claim above) were
  already computed on this contaminated population. Full findings in
  `docs/audit_log.md`.
- Fixed at the split stage: `src/features/train_val_split.py` now filters
  to `label_defined & (prev_flag == 0)` before assigning train/val — see
  `docs/decisions/003-eligibility-filter.md`. Split drops from 12,682,421
  to 12,111,689 rows (exactly Phase 1's eligible-non-holder count from
  2026-08-02). Rebuilt all three Phase 2 feature files against the
  corrected split, then re-ran `notebooks/02-04_feature_check_group*.ipynb`
  to get honest numbers.
- Numbers moved, not just noise: `product_count_prev`'s correlation with
  adoption rose from ~0.13 to **~0.163** (the contaminated rows were
  *diluting* its signal, not inflating it — those rows have high product
  counts but a trivially-False label). Group 1 and demographics moved only
  slightly (tenure ~0.05→0.059, activity ~0.08→0.083, age ~0.033→0.035).
  Feature ranking order unchanged; magnitude wasn't safe to assume. New
  concept (eligibility/population definition) logged in
  `docs/concepts_log.md`.
- Other `/audit` findings (no baseline model yet, no held-out test set, no
  merge-safety tests, CSV intermediates, env pinning, eyeballed cutoffs,
  docs-outpacing-modeling, and a correlation-vs-nonmonotonic-feature issue
  with `age`) left open for now — not addressed this session, tracked in
  `docs/audit_log.md`.
- Next: assemble `train.csv`/`val.csv` from the corrected split + three
  feature files + label, then baseline logistic regression + LightGBM.

### 2026-09-12 — Parquet migration + first tests, addressing two open /audit findings

- Discussed the open `/audit` findings before starting new modeling work.
  Found `docs/audit_log.md` itself was stale: [contaminated-negative-class]
  and [stale-correlation-numbers-already-contaminated] were already fixed
  by the 2026-09-11 eligibility-filter session but still marked STILL OPEN
  in the log (the fix happened after that audit entry was written) — logged
  a dated correction rather than re-doing the fix.
- Migrated all five `data/processed/` intermediates from CSV to Parquet
  (`adoption_labels_tjcr`, `train_val_split`, `features_tenure_activity`,
  `features_product_count`, `features_demographics`) — addresses
  [csv-intermediate-files]. Updated all five `src/features/*.py` build
  scripts and all four notebooks (`01_eda` through
  `04_feature_check_group3`) to read/write Parquet; dropped the
  `dtype=`/`parse_dates=` workarounds these reads used to need, since
  Parquet preserves dtypes (including pandas `Period[M]` and nullable
  `boolean`, confirmed with a round-trip test first). Re-ran the full
  pipeline and re-executed all four notebooks end to end — every number
  reproduced exactly (e.g. `product_count_prev` correlation: 0.163054
  before and after). `data/processed/` dropped from ~2.9 GB to ~395 MB.
  Deleted the old CSVs. New concept logged in `docs/concepts_log.md`.
- Added `pytest` + a `tests/` directory (12 tests) covering
  `build_adoption_label.py`'s `build_label()` (adoption, already-holder,
  non-adoption, undefined-label, and gap-month scenarios on synthetic data)
  and each feature script's `attach_profile()` t-1 join — addresses
  [no-tests-on-label-logic] (partially: still no CI, tests are run
  manually). Also added a runtime `assert len(merged) == len(input)` right
  after the merge in `build_label()` and each `attach_profile()`, so a
  future regression fails loudly during a real run, not just in a test.
  Added `pytest.ini` (`pythonpath = src`) and `.vscode/settings.json`
  (`python.testing.pytestEnabled`) so VSCode's built-in Test Explorer
  discovers and runs these directly. New concept logged in
  `docs/concepts_log.md`.
- Updated `docs/audit_log.md` with a 2026-09-12 status entry marking
  [contaminated-negative-class], [stale-correlation-numbers-already-contaminated],
  and [csv-intermediate-files] RESOLVED, and [no-tests-on-label-logic]
  PARTIALLY ADDRESSED. Still open: [no-baseline-model-yet],
  [no-held-out-test-set], [env-reproducibility], [eyeballed-cutoffs],
  [docs-outpacing-modeling], [correlation-yardstick-vs-nonmonotonic-feature].
- Next: still assemble `train.csv`/`val.csv` from the split + three feature
  files + label, then baseline logistic regression + LightGBM. Before that
  (per this session's discussion), consider a 3-way split (add a held-out
  test period) so the eventual baseline number isn't the same one used for
  model selection — addresses [no-held-out-test-set], the other flagged
  priority item.

### 2026-09-13 — 3-way train/val/test split, addressing [no-held-out-test-set]

- Discussed and decided the open `/audit` finding from 2026-09-11:
  val was going to be used both to pick between LR/LightGBM (and tune
  hyperparameters) and to report the final baseline number, which biases
  that number optimistically. Explained the train/val/test concept and
  alternatives (time-series CV, 2-way split with a caveat) before deciding;
  full reasoning in `docs/decisions/004-three-way-split.md`.
- Repartitioned `src/features/train_val_split.py`: test = last 3 labeled
  months (2016-03/04/05, unchanged from the old val window — held out,
  reported once), val = the 2 months before that (2016-01/02, for model
  selection), train = the remaining 11 months (2015-02 to 2015-12). New
  counts: train 7,694,326 rows / 48,696 adoptions (0.633%), val 1,751,740 /
  7,673 (0.438%), test 2,665,623 / 12,749 (0.478%) — test's counts match
  the old val bucket exactly, as expected.
- Rebuilt all three Phase 2 feature files against the corrected split and
  re-executed notebooks 02–04 (train split only, now 11 months instead of
  13): correlations moved slightly but ranking and magnitudes held
  (product_count_prev 0.163→0.166, tenure 0.059→0.060, activity
  0.083→0.084, age 0.035→0.036) — expected drift from a smaller train
  window, not a red flag.
- Updated `tests/test_train_val_split.py` for the new three-way boundary
  (13 tests now, all passing). New concept logged in
  `docs/concepts_log.md`; `docs/audit_log.md` updated marking
  [no-held-out-test-set] RESOLVED.
- Noted but not fixed this session: `src/reports/generate_technical_deepdive.py`
  still describes the old 2-way split with stale row counts — needs a
  refresh pass, not urgent since it doesn't block modeling work.
- Next: assemble train/val/test feature tables (split + three feature
  files + label, joined on `ncodpers`/`fecha_dato`) into modeling-ready
  frames, then baseline logistic regression + LightGBM — fit on train,
  compare/tune on val, compute the final precision@K number on test
  exactly once.

### 2026-09-13 (cont'd 3) — `/audit`, then environment + README fixes

- Ran a full `/audit`. Top finding: `scikit-learn` and `lightgbm` — the two
  libraries baseline modeling needs next — weren't actually installed in
  this environment despite being in `requirements.txt`, a recurrence of the
  same env-drift problem first caught on 2026-08-10. Second finding:
  `README.md`'s Status line still said "Phase 0 — scaffolding in
  progress," badly understating actual progress. Full findings (including
  carried-over items, one resolved this session) in `docs/audit_log.md`.
- Fixed both: ran `pip install -r requirements.txt`, which surfaced a real
  follow-on break (resolved `numpy` 1.26.1→2.4.6 broke `shap`'s
  `opencv-python` dependency, an old pre-numpy-2 build) — fixed by
  upgrading `opencv-python` to 5.0.0.93. Confirmed every required package
  imports cleanly and all 13 tests still pass, then pinned every line in
  `requirements.txt` to the exact confirmed-working versions instead of
  bare names, closing the longer-standing [env-reproducibility] finding
  too. New concept (dependency pinning) logged in `docs/concepts_log.md`.
- Rewrote `README.md`'s Status section to point at `ROADMAP.md`'s
  status-at-a-glance block instead of duplicating a hand-maintained phase
  line that kept going stale.
- Still open from the audit, not addressed this session:
  [no-baseline-model-yet] (now the clear next-session priority),
  [eyeballed-cutoffs], [docs-outpacing-modeling],
  [correlation-yardstick-vs-nonmonotonic-feature].
- Next: no more infra/doc sessions — assemble train/val/test feature
  tables and get a first baseline (logistic regression + LightGBM) running
  end to end, evaluated with precision@K vs. random targeting.

### 2026-09-15 — Assembled the modeling table

- Built `src/features/build_modeling_table.py`: starts from
  `train_val_split.parquet` (the eligible, labeled population + its
  train/val/test tag) and left-joins in the adoption label and all three
  Phase 2 feature files on `(ncodpers, fecha_dato)`. Every join used
  pandas' `merge(..., validate="one_to_one")` in addition to the existing
  row-count assert, catching a duplicate key on either side before it could
  silently fan out rows — new technique logged in `docs/concepts_log.md`.
- Every join matched 100% (all four sources were built against the exact
  same population, so no NaNs introduced by the joins themselves). Output:
  `data/processed/modeling_table.parquet`, 12,111,689 rows x 22 columns.
  Per-split adoption rates reproduced exactly what was logged when the
  split was built (train 0.633%, val 0.438%, test 0.478%), confirming
  nothing was dropped, duplicated, or miscounted in the assembly.
- Added `tests/test_build_modeling_table.py` (3 tests: row-count-preserving
  join with an unmatched row filled as NaN, duplicate-key detection via
  `validate=`, and a full `assemble()` smoke test on synthetic data) — full
  suite now 16 tests, all passing.
- Next: baseline logistic regression + LightGBM on `modeling_table.parquet`
  — fit on train, compare on val, report precision@K on test exactly once.

### 2026-09-15 (cont'd) — Audit review + age correlation re-check

- Reviewed the open `/audit` findings with Adam and picked one to act on
  now: [correlation-yardstick-vs-nonmonotonic-feature] (age's Pearson
  correlation understating its real relationship with adoption, flagged
  2026-09-11). The other three open items ([no-baseline-model-yet],
  [eyeballed-cutoffs], [docs-outpacing-modeling]) were left as-is — the
  first resolves naturally once baseline modeling starts, the other two
  don't block anything right now.
- Built a per-bin lift table for `age_years` on the train split (12
  age buckets): adoption rate ranges from 0.04x the overall rate at age
  20-25 up to 2.04x at 45-50, back down to 0.29x at 80+ - confirmed the
  non-monotonic pattern Phase 1 EDA already noted is real and far stronger
  than Pearson's 0.0356 ("weak") suggested. Considered Spearman rank
  correlation as an alternative fix and rejected it - it only handles
  monotonic-but-nonlinear relationships, not a curve that rises and falls,
  so it would have made the same mistake as Pearson.
- Since a plain linear model (logistic regression, part of the upcoming
  baseline) can't use a non-monotonic pattern from `age_years` alone,
  added `age_years_sq` (age centered on the train-only mean, then squared)
  to `build_features_demographics.py` - lets LR fit a parabola instead of
  a flat line. LightGBM needs no change; tree splits already capture
  non-monotonic patterns natively. New concept logged in
  `docs/concepts_log.md`.
- Rebuilt `features_demographics.parquet` and `modeling_table.parquet`
  (now 23 columns) - row counts, match rates, and all other feature values
  reproduced exactly, only the new column changed. Full 16-test suite
  still passes. `docs/audit_log.md` updated marking
  [correlation-yardstick-vs-nonmonotonic-feature] RESOLVED.
- Next: baseline logistic regression + LightGBM on the updated
  `modeling_table.parquet` — fit on train, compare on val, report
  precision@K on test exactly once.

### 2026-09-16 — Baseline logistic regression

- Built `src/models/baseline_logistic_regression.py`: fits on the 7.69M-row
  train split using 16 of the Phase 2 features (`renta_log` instead of the
  collinear `renta_imputed`), with continuous features standardized on
  train-only statistics and `class_weight="balanced"` to counter the
  ~0.6% adoption rate. Both concepts (logistic regression as a baseline,
  class weighting for imbalance) explained before coding and logged in
  `docs/concepts_log.md`.
- Deliberately scoped small: this is a sanity check, not the formal
  evaluation. Result: ROC-AUC 0.906 (train) / 0.912 (val), ~14-17x lift in
  the top 1% of customers by predicted score. Coefficient signs matched
  expectations — `activity_index` and `product_count_prev` strongly
  positive, `age_years` positive with `age_years_sq` negative (traces the
  45-50 adoption peak found last session as a downward parabola).
- Added `tests/test_baseline_logistic_regression.py` (3 tests: feature
  selection/target casting, train-only scaler fitting, top-K lift sanity)
  — full suite now 19 tests, all passing.
- Deliberately not done today (next session): LightGBM on the same
  train/val split, then the formal precision@K evaluation (fixed contact
  budget K, both models vs. random targeting) reported once on test, then
  `reports/02_baseline_model.md`.
- Next: LightGBM baseline on `modeling_table.parquet`, same train/val
  split as today, so it's directly comparable to this logistic regression
  result.

### 2026-09-16 (cont'd) — Baseline LR notebook + refreshed recap/deep-dive PDFs

- Built `notebooks/05_baseline_logistic_regression.ipynb`, walking through
  the baseline step by step by importing and reusing the actual functions
  from `src/models/baseline_logistic_regression.py` (rather than
  re-deriving the logic inline) - includes an ROC curve, a predicted-
  probability histogram split by actual outcome, a coefficient bar chart,
  and a lift-vs-contact-budget curve across several K values. Executed
  end to end via `jupyter nbconvert --execute`, no errors.
- Both `reports/Project_Recap.pdf` and `reports/Technical_Deep_Dive.pdf`
  had gone stale since their last refresh on 2026-08-17 (still describing
  only Group 1 features and a 2-way split) - caught up both to cover
  Groups 2-3, the eligibility-filter audit fix, the 3-way split, modeling
  table assembly, the age_years_sq fix, and today's baseline LR results.
  Recap gained plain-language steps 9-13; deep-dive gained Part 4 topics
  11-15 (group-wise imputation, log-transform, the audit fix, per-bin
  lift tables, merge-safety/testing) and moved logistic regression + class
  weighting from "planned" (Part 5) to "implemented," leaving only
  LightGBM in the still-planned section (now Part 6).
- Next: LightGBM baseline on `modeling_table.parquet`, same train/val
  split as the logistic regression baseline, for a direct comparison.

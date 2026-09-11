# Roadmap

5 phases, ~16 weeks. This is a living document — update checkboxes and add a dated
entry to the working log every session, even a short one.

> **Status at a glance (update this block every session — keep it to ~5 lines):**
> **Phase 1 is complete.** Service A is decided (credit card,
> `ind_tjcr_fin_ult1`; see `docs/decisions/001-service-a-product-choice.md`),
> the adoption label is built (`data/processed/adoption_labels_tjcr.csv`,
> gitignored — rerun `src/features/build_adoption_label.py` if missing), and
> the EDA notebook + findings write-up are done (`notebooks/01_eda.ipynb`,
> `reports/01_eda_findings.md`) — strongest signals found: activity index,
> tenure, segmento.
> **Time-respecting train/val split is done** (`data/processed/train_val_split.csv`,
> gitignored — rerun `src/features/train_val_split.py` if missing; last 3
> labeled months as val, see `docs/decisions/002-train-val-split.md`).
> **Phase 2 feature engineering: Groups 1-3 done** — tenure/activity, product
> count (strongest signal so far, ~0.13 correlation), and demographics
> (age/sex/segmento/income) are all built and sanity-checked.
> `canal_entrada` (162-category channel column) is deliberately deferred,
> not built — revisit only if baseline model evaluation suggests it's
> needed. **Next up:** assemble train.csv/val.csv from the split + all
> three feature files + label, then baseline logistic regression +
> LightGBM. Full detail is in the Working Log below.

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
- [ ] Baseline logistic regression + LightGBM
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

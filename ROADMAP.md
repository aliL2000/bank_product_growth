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
> **Next up:** Phase 2 feature engineering. Full detail is in the Working Log
> below.

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
- [ ] Feature engineering: tenure, product count, channel activity, demographics
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

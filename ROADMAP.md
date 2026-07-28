# Roadmap

5 phases, ~16 weeks. This is a living document — update checkboxes and add a dated
entry to the working log every session, even a short one.

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
- [ ] Finalize which product is "Service A" (log decision in `docs/decisions/`)
- [ ] Build the adoption label (lacked product in month t-1, gained it in month t)
- [ ] First EDA notebook — adoption rate over time, by segment
- [ ] Write `reports/01_eda_findings.md`

## Phase 2 — Baseline Model (Weeks 5–7)
- [ ] Time-respecting train/val split (train on earlier months, validate on later)
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

# Roadmap

5 phases, ~16 weeks. This is a living document — update checkboxes and add a dated
entry to the working log every session, even a short one.

## Phase 0 — Setup (Week 1)
- [x] Scaffold repo structure
- [x] Write `.gitignore`, `requirements.txt`
- [x] Draft `README.md`, `docs/dataset.md`, `docs/problem_statement.md`
- [x] Write `src/data/load_data.py` loader skeleton
- [ ] Download `train_ver2.csv` / `test_ver2.csv` into `data/raw/`
- [ ] Set up GitHub remote and push

## Phase 1 — Understand the Data (Weeks 2–4)
- [ ] Run `load_data.py` against real data, check shape/dtypes/memory footprint
- [ ] Profile missingness across all 24 profile columns
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

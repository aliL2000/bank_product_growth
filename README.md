# Product Adoption & Growth Analytics for Financial Services

## One-line pitch
Given a bank offering multiple financial products/services, predict which existing
customers are most likely to adopt an *additional* product next, and quantify what
actually drives adoption — so the business can target the right users with the right
offer instead of blasting everyone.

## Business framing
Bank X offers Service A (e.g. a credit card, payroll account, or investment product).
Many existing customers who could benefit from Service A aren't using it. Given
everything we know about a customer's current relationship with the bank (products
held, tenure, channel activity, demographics, transaction behavior), can we (1)
predict who's likely to adopt Service A next, (2) explain why, and (3) turn that into
a prioritized, ROI-aware targeting list — instead of contacting everyone equally.

This is a cross-sell / next-best-product propensity modeling problem, framed the way
a bank's growth/marketing analytics team would actually approach it: as a limited
marketing budget allocation problem, not a "classify everyone accurately" problem.

## Dataset
**Santander Product Recommendation** (Kaggle):
https://www.kaggle.com/c/santander-product-recommendation

- ~13M+ rows, ~950,000 customers, 17 monthly snapshots (Jan 2015–Jun 2016)
- 24 customer profile/behavior columns + 24 binary product-ownership flags
- Not auto-downloadable — requires a free Kaggle account and accepting the
  competition rules. Download `train_ver2.csv` and `test_ver2.csv`, place them in
  `data/raw/`.
- See `docs/dataset.md` for the full data dictionary and download steps.

**Service A is credit card (`ind_tjcr_fin_ult1`)** — decided 2026-07-29, see
`docs/decisions/001-service-a-product-choice.md` for the full reasoning
(payroll account and mutual funds were the alternatives considered).

## Project structure

```
product_growth/
├── README.md
├── ROADMAP.md
├── docs/
│   ├── dataset.md
│   ├── problem_statement.md
│   └── decisions/
├── data/{raw, interim, processed}/   (gitignored contents)
├── notebooks/
├── src/{data, features, models, viz}/
├── reports/
└── requirements.txt
```

## Roadmap (5 phases, ~16 weeks — full detail in ROADMAP.md)
0. Setup — repo scaffold, dataset picked, problem statement written
1. Understand the data — EDA, data quality, define adoption label, pick Service A
2. Baseline model — time-respecting split, LightGBM/logistic baseline,
   precision@K / lift as the metric (not raw accuracy — this is a budget-targeting
   problem, not a classify-everyone problem)
3. Explainability & segmentation — SHAP, plain-English adoption drivers,
   under-served high-propensity segment
4. Targeting strategy & simulated ROI — cost-per-contact vs. value-per-adoption,
   model-score targeting vs. simple-rule vs. everyone
5. Polish — lightweight Streamlit dashboard, executive summary, interview cheat sheet

## Working agreement
- Long-running, incremental — small real commits each session, not a one-shot build.
- Update a dated working log in `ROADMAP.md` every session.
- Time-respecting train/val split always (train on earlier months, validate on
  later — never shuffle across time).
- State limitations plainly: this is Spanish retail-bank data, not portable to a real
  employer's numbers as-is; Phase 4 ROI claims are simulated assumptions, not proven
  causal effects.

## Status
🟡 Phase 0 — scaffolding in progress.

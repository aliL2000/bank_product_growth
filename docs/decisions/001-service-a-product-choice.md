# Decision Record: Service A product choice

## Title
Service A = credit card (`ind_tjcr_fin_ult1`)

## Date
2026-07-29

## Context
Three candidate products were on the table for "Service A" (the product whose
adoption we're modeling): credit card (`ind_tjcr_fin_ult1`), payroll account
(`ind_nomina_ult1`), and mutual funds (`ind_fond_fin_ult1`). The rest of Phase 1
(the adoption label, the EDA) and everything downstream (features, model,
explainability, targeting/ROI) hangs off this choice, so it needed to be locked
in before going further.

## Decision
Credit card (`ind_tjcr_fin_ult1`).

## Why
- **Large addressable non-holder pool**: a month-by-month prevalence check across
  the full 17-month train file shows only ~3.7–5.8% of customers hold a credit
  card in any given month (highest in early 2015, drifting down toward ~3.7% by
  mid-2016) — so 94–96% of the customer base is a potential target in any given
  month. That's a healthy amount of both positive and negative signal for a
  propensity model.
- **Actionable / marketable**: credit card adoption is a product a bank's
  marketing or relationship team can realistically influence with an offer or
  outreach. Payroll account adoption, by contrast, is largely driven by a
  customer switching employers — something outreach can't cause — which would
  undercut the "actionable targeting" story in Phase 4.
- **Rich behavioral signal expected**: credit card usage is likely to correlate
  with a broad mix of existing engagement signals already in the data (activity
  index, product count, channel, income), giving more to work with for
  explainability (Phase 3) than a narrower or more externally-driven product.

## Alternatives considered
- **Payroll account (`ind_nomina_ult1`)**: rejected mainly because adoption is
  plausibly confounded by employer changes rather than bank-driven marketing —
  weakens the causal-adjacent story even though we're already careful to avoid
  overclaiming causality.
- **Mutual funds (`ind_fond_fin_ult1`)**: not yet numerically ruled out, but
  expected to be a smaller, more income/wealth-segment-concentrated population,
  likely giving less data to work with and a narrower addressable audience than
  credit card. Didn't compute its exact prevalence before deciding — credit card's
  case was strong enough on its own to not need a three-way numeric bake-off for
  this call.

## Consequences / what this affects downstream
- The adoption label (Phase 1 next step) will be built specifically around
  `ind_tjcr_fin_ult1`: non-holder in month t-1, holder in month t.
- `docs/dataset.md`'s Service A section and `README.md` should be updated to
  reflect this as a settled decision rather than an open candidate list.
- Phase 2 feature engineering, Phase 3 SHAP narrative, and Phase 4 ROI framing
  will all be told in terms of credit-card cross-sell specifically.

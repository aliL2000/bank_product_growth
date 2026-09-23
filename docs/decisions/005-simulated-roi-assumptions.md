# Decision Record: Simulated ROI assumptions for Phase 4

## Title
Base case: email/in-app channel at €0.50 per contact, €150 net value per
incremental adoption, 20% relative uplift from being contacted. Break-even
precision is 1.67%. **All three numbers are simulated assumptions, not real
bank economics.**

## Date
2026-09-23

## Context
Phase 4 compares three targeting strategies (model-score top-K, the Phase 3
segment business rule, contact-everyone) on simulated profit. Phase 2's
precision@K table can't choose a contact budget by itself because it has no
costs in it (`reports/02_baseline_model.md`: "there's no single 'right' K
without a real contact-capacity/cost constraint"). This record supplies those
costs.

The model predicts who *adopts*, not who adopts *because they were
contacted*. The dataset has no treatment/control structure
(`docs/problem_statement.md`), so contact's causal effect can't be measured
here and has to be assumed explicitly.

## Decision
Profit for a contact list of K customers:

```
profit(K) = UPLIFT × adopters_captured(K) × VALUE_PER_ADOPTION − K × COST_PER_CONTACT
```

| Assumption | Base case | Sensitivity sweep |
|---|---|---|
| Channel / cost per contact | Email/in-app, €0.50 | Outbound phone, €6.00 |
| Net value per incremental adoption | €150 | €50, €300 |
| Relative uplift from contact (*u*) | 20% | 5%, 10%, 40% |

Contacting a list is profitable only when `precision × u ≥ cost / value`,
i.e. base-case break-even precision = 0.50 / (0.20 × 150) = **1.67%**.

All values live in `src/models/roi_assumptions.py`, the only place Phase 4
code reads them from.

## Why
- **Email as headline**: at €0.50 the break-even (1.67%) falls inside the
  range the model actually produces (8.6% precision at a 0.1% budget, 5.1%
  at 5%), while contact-everyone (0.48% = the base rate) sits below it. So
  the choice of targeting strategy decides whether the campaign makes money,
  which is the comparison Phase 4 exists to make. Phone at €6 has a 20%
  break-even, above the model's best precision, so it's unprofitable at any
  budget. That's reported as a sensitivity result, not hidden.
- **€150**: middle of the commonly cited first-year net-margin range for a
  credit card (interchange + interest − credit losses − card costs).
  Deliberately not a multi-year lifetime value, which would flatter every
  strategy including contact-everyone.
- **20% relative uplift**: a modest middle value. It's the least knowable
  number of the three, so the report must show the sweep, not only the base
  case.

## Alternatives considered
- **No uplift term (treat every captured adopter as caused by the
  contact)**: rejected. It counts customers who would have adopted anyway
  as campaign wins, which overstates ROI and is the standard mistake in
  propensity-based ROI claims.
- **Absolute uplift (+x percentage points for everyone contacted)**:
  rejected. It makes each contact's value independent of its score, so
  ranking by propensity wouldn't matter at all. That contradicts the
  premise being tested rather than testing it.
- **Uplift modeling (estimate who is persuadable)**: the right tool for
  real deployment, but it needs experimental (contacted vs. not-contacted)
  data this dataset doesn't have. Named as a limitation instead.

## Consequences / what this affects downstream
- Relative uplift makes incremental value proportional to propensity, so
  ranking by model score is optimal by construction. That's an assumption,
  not a finding. Real campaigns hit "sure things" (would adopt anyway) at
  the top of the list, where true uplift is often *lowest*.
  `reports/04_targeting_roi.md` must say this plainly.
- The Phase 4 strategy comparison runs on **test** (the precision@K numbers
  already reported there, `docs/decisions/004-three-way-split.md`). No
  retuning of the model happens against ROI.
- Any headline profit figure in the report or resume bullets must carry the
  "simulated" label and quote the break-even precision alongside it.

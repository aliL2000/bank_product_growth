# Phase 4: Targeting Strategy & Simulated ROI — Findings

Source: `src/models/targeting_roi.py` (assumptions from
`src/models/roi_assumptions.py`, set in
`docs/decisions/005-simulated-roi-assumptions.md`). Purpose: turn the
Phase 2 ranking and the Phase 3 segment into a decision. Who should the
bank contact about a credit card, how many people, and does it make money?

> **Every euro figure in this report is simulated.** Contact cost, value
> per adoption and uplift from contact are assumptions, not bank data
> (decision record 005). Each headline number is quoted with its
> break-even precision, and the base case is always shown next to the
> sensitivity sweep, never alone.

All numbers are on **test** (2,665,623 customer-months, 0.478% base rate).
Nothing was tuned on test. The model is the Phase 2 LightGBM baseline with
its original settings. Each scenario's contact budget is chosen on **val**
and then applied to test unchanged (`docs/decisions/004-three-way-split.md`).

## The yardstick: simulated profit and break-even precision

```
profit(list) = uplift × adopters_in_list × value_per_adoption − list_size × cost_per_contact
```

A list makes money only if its precision is at least
`cost / (uplift × value)`, the **break-even precision**. Base case: email
or in-app at €0.50 per contact, €150 net value per incremental adoption,
20% relative uplift. That gives a **1.67% break-even**.

Three strategies are compared:

| Strategy | Who gets contacted |
|---|---|
| **Model top-K** | The top-K customers by LightGBM score. K is chosen on val (below). |
| **Segment rule** | Every customer in the Phase 3 segment: active, `particulares`, exactly one existing product, aged 35–64. A fixed list. |
| **Contact everyone** | The whole population. |

## How many to contact: the profit curve

Walking down the model's ranking, each extra contact pays for itself only
while *that customer's* adoption chance is above break-even. Profit
therefore rises, peaks, and falls. It peaks well before the list's
**average** precision reaches break-even. On val at a 10% budget, the
list's average precision is still 3.2%, but profit is already falling:
the customers added between 7.5% and 10% convert at about 1.5%, below the
1.67% needed.

The budget is found on val's exact curve (every list size, not a grid):
**7.74% of customers**. Test's own peak is 8.36%. That number is shown for
context only. Choosing the budget on test and then reporting test profit
at it would overstate the result. The two peaks are close, and the profit
curve is flat around them (see
`reports/targeting_profit_curve.csv`), so the val-chosen budget gives up
little.

A list must have at least **1,000 contacts** to count as a campaign.
Without that floor, when no real campaign can pay, the exact maximum lands
on 2–3 customers where one happened to adopt ("50% precision"). The floor
turns those cases into the honest answer: don't run the campaign.

## Base case: strategy comparison on test

| Strategy | Contacted | Adopters in list | Precision | Simulated profit |
|---|---|---|---|---|
| Model top-K @ val-chosen 7.74% | 206,276 | 8,368 | 4.06% | **+€147,902** |
| Segment rule | 177,720 (6.67%) | 672 | 0.38% | **−€68,700** |
| Model top-K @ the segment's list size | 177,720 | 7,737 | 4.35% | +€143,250 |
| Contact everyone | 2,665,623 | 12,749 | 0.48% | −€950,342 |

*Break-even precision: 1.67%.*

The third row is the fair head-to-head. It gives the model exactly the
segment rule's list size, so the comparison is about *who* gets picked,
not *how many*. With the same 177,720 contacts, the model finds **11.5x
more adopters** (7,737 vs. 672).

## Finding: the Phase 3 segment is not worth contacting

This is the main surprise. Phase 3 found the segment converts at about 5x
the rate of *other one-product customers*, and that was correct. But
one-product customers as a whole convert at only ~0.07%. Five times a very
small number is still small. In absolute terms the segment converts at
**0.38%**, which is *below* the population average (0.48%) and far below
the 1.67% break-even.

Phase 3 asked whether the rule was redundant with the model or a
different signal worth combining with it. Under any cost structure tested
here, the answer is neither: the rule doesn't pay on its own. "Promising
compared with similar under-served customers" and "worth paying to
contact" are different questions. Phase 3 answered the first; this report
answers the second.

That doesn't make the Phase 3 finding useless. It's still a real,
interpretable pattern about *who* adopts among single-product customers.
It could be useful for a cheaper channel than the ones tested here, or for
product design. It just isn't a contact list.

## Sensitivity: does the conclusion survive other assumptions?

All 24 combinations of the decision-005 sweep values (cost: email €0.50 /
phone €6; value: €50 / €150 / €300; uplift: 5% / 10% / 20% / 40%). Each
has its own val-chosen budget. Full results:
`reports/targeting_sensitivity_sweep.csv`.

**Email (€0.50 per contact):**

| Value | Uplift | Break-even | Budget (val) | Model | Segment rule | Contact everyone |
|---|---|---|---|---|---|---|
| €50 | 5% | 20.0% | none | €0 | −€87,180 | −€1,300,940 |
| €50 | 10% | 10.0% | 0.07% | −€97 | −€85,500 | −€1,269,067 |
| €50 | 20% | 5.0% | 2.20% | +€11,598 | −€82,140 | −€1,205,322 |
| €50 | 40% | 2.5% | 4.18% | +€67,496 | −€75,420 | −€1,077,832 |
| €150 | 5% | 6.67% | 0.99% | +€2,784 | −€83,820 | −€1,237,194 |
| €150 | 10% | 3.33% | 3.93% | +€36,579 | −€78,780 | −€1,141,577 |
| **€150** | **20%** | **1.67%** | **7.74%** | **+€147,902** | **−€68,700** | **−€950,342** |
| €150 | 40% | 0.83% | 12.80% | +€432,580 | −€48,540 | −€567,872 |
| €300 | 5% | 3.33% | 3.93% | +€36,579 | −€78,780 | −€1,141,577 |
| €300 | 10% | 1.67% | 7.74% | +€147,902 | −€68,700 | −€950,342 |
| €300 | 20% | 0.83% | 12.80% | +€432,580 | −€48,540 | −€567,872 |
| €300 | 40% | 0.42% | 21.61% | +€1,105,107 | −€8,220 | +€197,069 |

**Phone (€6 per contact):** the model runs no campaign (€0) in 9 of 12
scenarios, loses €1,164 in 2 borderline ones (break-even 10%), and pays
in only one: €300 value with 40% uplift (5% break-even, 2.20% budget,
**+€139,170**). The segment rule loses €1.0–1.1M and contact-everyone
loses €14–16M in every phone scenario.

What the sweep shows:

- **The segment rule loses money in all 24 scenarios.** Its 0.38% precision
  clears break-even only if break-even falls below 0.38%. No tested
  combination gets that low.
- **The model never loses meaningfully.** It's profitable in every email
  scenario with break-even at or below 6.67%. Its worst result is −€1,164,
  in the borderline cases where break-even (10%) sits just above its best
  precision (~9%). There, val found a tiny list that was barely profitable,
  and on test it was roughly break-even. Read those rows as "don't bother",
  not as a loss.
- **Contact-everyone pays in exactly one scenario** (€300 × 40%), where
  break-even (0.42%) drops below the 0.48% base rate. Even then the model
  earns **5.6x more** (€1.11M vs. €197K), because it skips the customers
  who don't pay for their own contact.
- **Only break-even precision decides the list.** Profit =
  `u·V × (adopters − list_size × break_even)`, so scenarios with the same
  break-even pick the same budget, and their profits differ only by the
  factor u·V. For example, email/€50/20% and phone/€300/40% both have a 5%
  break-even and both pick 2.20%, and the phone profit (€139,170) is
  exactly 12x the email one (€11,598). The 24 scenarios reduce to 15
  distinct break-evens.
- **Phone is only viable in the most optimistic corner.** At €6 per
  contact, the model's ~9% best precision is below break-even unless value
  and uplift are both at their highest.

The **ranking** of strategies is robust: model ≥ don't contact (within
€1.2K in the three borderline scenarios) > segment rule > contact
everyone. The one exception is €300 × 40%, where contact-everyone turns
positive but still trails the model. The **size** of the model's profit is not. It ranges
from €0 to €1.1M depending on assumptions no one here can check. Quote the
base case with its break-even, and the range with it.

## Caveats

- **Ranking by score is optimal because of an assumption, not a finding.**
  Relative uplift means each contact's value is proportional to its
  adoption chance, so ranking by propensity is optimal by construction
  (decision record 005). Real campaigns often find the top of a propensity
  list full of "sure things" who would have adopted anyway, where the true
  effect of contacting them is *smallest*. Finding the persuadable
  customers needs uplift modeling on experimental data (contacted vs. not
  contacted), which this dataset doesn't have. The sweep varies *how big*
  uplift is. It never varies *who* is persuadable.
- **No real economics.** Cost, value and uplift are placeholders chosen to
  be plausible (decision record 005). The value is deliberately
  first-year margin, not lifetime value, which would flatter every
  strategy.
- **One snapshot, one model fit.** Test covers a single later period. The
  profit figures carry sampling noise that isn't formally quantified here.
  As a rough guide, binomial noise on the base case's ~8,400 captured
  adopters is about ±90 adopters (one standard deviation), or about ±€2.7K
  of profit. Small next to the gaps between strategies, but not zero.
- **Test was read 24+ times, but nothing was chosen from it.** The model,
  the budget in every scenario, and the segment definition were all fixed
  on train or val. Test only reports. The one test-based peak (8.36%) is
  labelled as context and not used.
- **The segment's age edges.** The Phase 3 age bands use right-closed
  intervals (`pd.cut` default), and ages are whole years. So "35–64" in
  practice covers ages **36–65**. This report keeps Phase 3's exact
  definition so the two reports agree. A one-year shift at each edge
  wouldn't close a gap between 0.38% precision and a 1.67% break-even.
- **Individual top scores overstate propensity** (Phase 3 calibration
  finding). That doesn't affect these results, which use observed
  adoptions on test, not predicted probabilities. But it's why the budget
  isn't set by "contact everyone whose score is above 1.67%".

## Business narrative (plain English)

A targeted email campaign built on the model's ranking is the only
strategy tested that reliably makes money. Under middle-of-the-road
assumptions, contacting the top ~8% of customers returns about €148K in
simulated profit. Contacting everyone loses nearly €1M, because 99.5% of
people won't adopt, and each of them still costs a contact.

The most intuitive business rule from Phase 3, "reach out to active,
mid-career customers who hold just one product", sounds like good
targeting but loses money under every assumption tested. Those customers
are more promising *than people like them*, but still far less likely to
adopt than the customers the model picks. Given the same number of
contacts, the model finds more than eleven times as many new cardholders.

The exact profit depends on numbers the bank would need to supply (what a
new card is really worth, and how much an email actually changes
behavior). Phone outreach only works in the most optimistic scenario. The
recommendation, email the model's top list and not the segment or the
whole base, holds across every scenario. The next step for a real
deployment would be a controlled test that measures uplift directly.

## Implications for Phase 5

- The executive one-pager's headline: model-targeted email, ~€148K
  simulated at a 1.67% break-even, versus −€950K for contact-everyone.
  Include the range across scenarios and the "simulated" label.
- The segment-rule result is a strong interview story: a sensible-looking
  rule that doesn't pay, and the relative-vs-absolute lift reason why.
- A dashboard could let a viewer move the cost, value and uplift sliders
  and watch the best budget and profit update. The profit curve is cheap
  to recompute from saved scores.

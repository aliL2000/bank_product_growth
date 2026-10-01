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

All numbers are on **test**: 3 months (2016-03 to 2016-05), 2,665,623
customer-months, **901,395 distinct customers**, 0.478% base rate. Nothing
was tuned on test. The model is the Phase 2 LightGBM baseline with its
original settings. Each scenario's contact budget is chosen on **val** and
then applied to test unchanged (`docs/decisions/004-three-way-split.md`).

## Unit of analysis: contacts are customer-months

The modeling table has one row per **customer per month**. Each month the
model scores every eligible customer, and "contacting" a row means sending
that customer one email that month. So the campaign simulated here is a
**monthly** campaign run for 3 months. The same customer can be emailed
in more than one month, and many are. Throughout this report, **"contacts"
means emails sent (customer-months)** and **"customers" means distinct
people**. Ranking the three months together or each month separately
gives the same result (€147,902 in the base case either way), so pooling
the months doesn't change which rows get picked.

## The yardstick: simulated profit and break-even precision

```
profit(list) = uplift × adopters_in_list × value_per_adoption − contacts × cost_per_contact
```

A list makes money only if its precision is at least
`cost / (uplift × value)`, the **break-even precision**. Base case: email
or in-app at €0.50 per contact, €150 net value per incremental adoption,
20% relative uplift. That gives a **1.67% break-even**.

This formula credits **every** contact with the same 20% uplift, including
the 2nd and 3rd monthly email to the same person. That's the generous end.
A stricter **first-contact-only** version is reported next to it: every
email still costs €0.50, but only adoptions on a customer's *first*
contact count. Repeat emails cost money and earn nothing. The truth for a
real campaign most likely sits between the two.

Three strategies are compared:

| Strategy | Who gets contacted each month |
|---|---|
| **Model top-K** | The top-K customer-months by LightGBM score. K is chosen on val (below). |
| **Segment rule** | Every customer in the Phase 3 segment: active, `particulares`, exactly one existing product, aged 35–64. A fixed list. |
| **Contact everyone** | Every eligible customer. |

## How many to contact: the profit curve

Walking down the model's ranking, each extra contact pays for itself only
while *that contact's* adoption chance is above break-even. Profit
therefore rises, peaks, and falls. It peaks well before the list's
**average** precision reaches break-even. On val at a 10% budget, the
list's average precision is still 3.2%, but profit is already falling:
the contacts added between 7.5% and 10% convert at about 1.5%, below the
1.67% needed.

The budget is found on val's exact curve (every list size, not a grid):
**7.74% of customer-months**, about **68,800 emails a month**. Test's own
peak is 8.36%. That number is shown for context only. Choosing the budget
on test and then reporting test profit at it would overstate the result.
Test profit at the val-chosen budget is €147,902, against €149,153 at
test's own peak, so the val-chosen budget gives up 0.8%.

A list must have at least **1,000 contacts** to count as a campaign.
Without that floor, when no real campaign can pay, the exact maximum lands
on 2–3 contacts where one happened to adopt ("50% precision"). The floor
turns those cases into the honest answer: don't run the campaign.

## Base case: strategy comparison on test

| Strategy | Contacts (3 months) | Distinct customers | Adopters in list | Precision | Profit (every contact earns uplift) | Profit (first contact only) |
|---|---|---|---|---|---|---|
| Model top-K @ val-chosen 7.74% | 206,276 | 79,154 | 8,368 | 4.06% | **+€147,902** | **+€40,232** |
| Segment rule | 177,720 (6.67%) | 67,430 | 672 | 0.38% | **−€68,700** | −€76,680 |
| Model top-K @ the segment's list size | 177,720 | 68,843 | 7,737 | 4.35% | +€143,250 | +€44,160 |
| Contact everyone | 2,665,623 | 901,395 | 12,749 | 0.48% | −€950,342 | −€1,124,432 |

*Break-even precision: 1.67%.*

The model's list reaches **79,154 people** (8.8% of customers). Most are
emailed repeatedly: **58,650 in all 3 months** and 9,822 in two. Only
4,779 of the 8,368 adoptions it captures (57%) happen on a customer's
first contact. The rest come after repeat emails, and that's why the
strict profit is about a quarter of the generous one. Note that the budget
was chosen under the generous accounting. The strict column shows what
*this plan* earns if repeat emails do nothing, not the best possible plan
under that assumption (which would contact fewer people, or contact each
person once).

The third row is the fair head-to-head. It gives the model exactly the
segment rule's list size, so the comparison is about *who* gets picked,
not *how many*. With the same 177,720 contacts, the model finds **11.5x
more adopters** (7,737 vs. 672). It stays ahead under either accounting.

## Finding: the Phase 3 segment is not worth contacting

This is the main surprise. Phase 3 found the segment converts at about 5x
the rate of *other one-product customers*, and that was correct. But
one-product customers as a whole convert at only ~0.07%. Five times a very
small number is still small. In absolute terms the segment converts at
**0.38%**, which is *below* the population average (0.48%) and far below
the 1.67% break-even.

Phase 3 left open whether the model already ranks this segment highly
(making the rule redundant) or underweights it (making it a signal worth
combining). The model's own ranking answers it directly: **only 3 of the
177,720 segment rows fall inside the model's top 7.74%**. The median
segment row sits at the **22.6th rank percentile**, so the model places
these customers above average but far below the contact cutoff. That
matches what the model learned: holding more products is one of its
strongest signals, and every segment member holds exactly one. So the
segment isn't a hidden signal the model missed. The model saw it, scored
it moderately, and the profit numbers confirm that was right.

"Promising compared with similar under-served customers" and "worth paying
to contact" are different questions. Phase 3 answered the first; this
report answers the second. The Phase 3 finding is still a real,
interpretable pattern about *who* adopts among single-product customers.
It could be useful for product design or a much cheaper channel than the
ones tested here. It just isn't a contact list.

## Sensitivity: does the conclusion survive other assumptions?

All 24 combinations of the decision-005 sweep values (cost: email €0.50 /
phone €6; value: €50 / €150 / €300; uplift: 5% / 10% / 20% / 40%). Each
has its own val-chosen budget. Full results:
`reports/targeting_sensitivity_sweep.csv`.

**Email (€0.50 per contact):**

| Value | Uplift | Break-even | Budget (val) | Model | Model (first contact only) | Segment rule | Contact everyone |
|---|---|---|---|---|---|---|---|
| €50 | 5% | 20.0% | none | €0 | €0 | −€87,180 | −€1,300,940 |
| €50 | 10% | 10.0% | 0.07% | −€97 | −€397 | −€85,500 | −€1,269,067 |
| €50 | 20% | 5.0% | 2.20% | +€11,598 | −€5,313 | −€82,140 | −€1,205,322 |
| €50 | 40% | 2.5% | 4.18% | +€67,496 | +€15,536 | −€75,420 | −€1,077,832 |
| €150 | 5% | 6.67% | 0.99% | +€2,784 | −€3,727 | −€83,820 | −€1,237,194 |
| €150 | 10% | 3.33% | 3.93% | +€36,579 | −€996 | −€78,780 | −€1,141,577 |
| **€150** | **20%** | **1.67%** | **7.74%** | **+€147,902** | **+€40,232** | **−€68,700** | **−€950,342** |
| €150 | 40% | 0.83% | 12.80% | +€432,580 | +€168,460 | −€48,540 | −€567,872 |
| €300 | 5% | 3.33% | 3.93% | +€36,579 | −€996 | −€78,780 | −€1,141,577 |
| €300 | 10% | 1.67% | 7.74% | +€147,902 | +€40,232 | −€68,700 | −€950,342 |
| €300 | 20% | 0.83% | 12.80% | +€432,580 | +€168,460 | −€48,540 | −€567,872 |
| €300 | 40% | 0.42% | 21.61% | +€1,105,107 | +€484,467 | −€8,220 | +€197,069 |

**Phone (€6 per contact):** the model runs no campaign (€0) in 9 of 12
scenarios and loses €1,164 in 2 borderline ones (break-even 10%). It pays
only in one: €300 value with 40% uplift (5% break-even, 2.20% budget,
**+€139,170**). Under first-contact-only accounting even that one turns
into **−€63,750**. The segment rule loses €1.0–1.1M and contact-everyone
loses €14–16M in every phone scenario.

What the sweep shows:

- **The segment rule loses money in all 24 scenarios.** Its 0.38% precision
  clears break-even only if break-even falls below 0.38%. No tested
  combination gets that low.
- **Under the generous accounting, the model never loses meaningfully.**
  It's profitable in every email scenario with break-even at or below
  6.67%. Its worst result is −€1,164, in the borderline cases where
  break-even (10%) sits just above its best precision (~9%). Those rows
  depend on the 1,000-contact floor (a 2,000 floor turns them into €0,
  "don't contact"). Read them as "don't bother", not as a loss.
- **Under first-contact-only accounting, the margin is much thinner.** The
  model stays profitable in the base case (+€40K) and in every email
  scenario with break-even at or below 2.5%. It loses a little (up to
  −€5.3K) in every email scenario with break-even of 3.33% or higher,
  because those budgets were set assuming repeat emails pay. It is never worse than the
  segment rule or contact-everyone.
- **Contact-everyone pays in exactly one scenario** (€300 × 40%), where
  break-even (0.42%) drops below the 0.48% base rate. Even then the model
  earns **5.6x more** (€1.11M vs. €197K).
- **Only break-even precision decides the list.** Profit =
  `u·V × (adopters − contacts × break_even)`, so scenarios with the same
  break-even pick the same budget, and their profits differ only by the
  factor u·V. For example, email/€50/20% and phone/€300/40% both have a 5%
  break-even and both pick 2.20%, and the phone profit (€139,170) is
  exactly 12x the email one (€11,598). The 24 scenarios reduce to 15
  distinct break-evens.
- **Phone is not viable.** At €6 per contact, the model's ~9% best
  precision is below break-even unless value and uplift are both at their
  highest, and even that case loses money once repeat calls earn nothing.

The **ranking** of strategies is robust under both accountings: model >
segment rule > contact everyone, with the model close to "don't contact"
in the borderline cases. The one exception is €300 × 40%, where
contact-everyone turns positive but still trails the model. The **size**
of the model's profit is not robust. It ranges from about €0 to €1.1M
depending on assumptions no one here can check, and the base case alone
spans €40K–€148K depending on whether repeat emails help. Quote the base
case with its break-even, and the range with it.

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
- **Repeat contact.** 74% of the model's customers are emailed in all 3
  months. The generous accounting assumes the 3rd email persuades as well
  as the 1st. The first-contact-only accounting assumes it does nothing.
  Neither models fatigue or annoyance, which would push results below the
  strict figure. A real deployment should cap contacts per customer.
- **No real economics.** Cost, value and uplift are placeholders chosen to
  be plausible (decision record 005). The value is deliberately
  first-year margin, not lifetime value, which would flatter every
  strategy.
- **One snapshot, one model fit.** Test covers a single later period. The
  profit figures carry sampling noise that isn't formally quantified here.
  As a rough guide, binomial noise on the base case's ~8,400 captured
  adopters is about ±90 adopters (one standard deviation), or about ±€2.7K
  of profit. That understates the real noise: the rows aren't independent
  (most of the list is the same ~59K people repeated each month). Still
  small next to the gaps between strategies.
- **Test was read many times, but nothing was chosen from it.** The model,
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

A targeted monthly email campaign built on the model's ranking is the only
strategy tested that reliably makes money. Under middle-of-the-road
assumptions, emailing the top ~69,000 customers each month (about 79,000
different people over three months) returns between about €40K and
€148K in simulated profit. The low end assumes follow-up emails to the
same person don't help; the high end assumes every email helps as much as
the first. Contacting everyone loses roughly €1M, because 99.5% of people
won't adopt, and each of them still costs a contact.

The most intuitive business rule from Phase 3, "reach out to active,
mid-career customers who hold just one product", sounds like good
targeting but loses money under every assumption tested. Those customers
are more promising *than people like them*, but still far less likely to
adopt than the customers the model picks. The model itself almost never
puts them on its list (3 out of 177,720). Given the same number of
contacts, the model finds more than eleven times as many new cardholders.

The exact profit depends on numbers the bank would need to supply (what a
new card is really worth, how much an email actually changes behavior,
and whether repeat emails help). Phone outreach doesn't pay. The
recommendation, email the model's top list and not the segment or the
whole base, holds across every scenario. The next step for a real
deployment would be a controlled test that measures uplift directly,
including whether a second or third email adds anything.

## Implications for Phase 5

- The executive one-pager's headline: model-targeted email, **€40K–€148K**
  simulated (first-contact-only to every-contact) at a 1.67% break-even,
  reaching ~79K customers over 3 months, versus about −€1M for
  contact-everyone. Include the scenario range and the "simulated" label.
- The segment-rule result is a strong interview story: a sensible-looking
  rule that doesn't pay, the relative-vs-absolute lift reason why, and the
  model's own ranking confirming it (3 of 177,720 in its list).
- A dashboard could let a viewer move the cost, value and uplift sliders
  (and a "repeat emails help: yes/no" toggle) and watch the best budget
  and profit update. The profit curve is cheap to recompute from saved
  scores.

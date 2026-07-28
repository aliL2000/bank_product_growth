# Problem Statement (draft)

> Draft written by Claude Code to structure the problem — replace with your own
> voice/narrative before using this in an interview context. This is scaffolding,
> not a finished writeup.

## The business problem
A retail bank sells many products to its existing customer base — checking and
savings accounts, credit cards, payroll deposit, mortgages, mutual funds, and more.
Most customers hold only a handful of the bank's products, even when a well-timed
offer for another product would benefit both the customer and the bank. Marketing
and relationship-management teams have limited capacity: they can't call, email, or
push a notification to every customer about every product every month. They need to
know **who to target with what, and roughly why it's worth it.**

## The specific question
For one chosen product ("Service A" — a candidate list is in `docs/dataset.md`,
final pick logged as a decision record):

> Among existing customers who do not currently hold Service A, which are most
> likely to newly adopt it in the next month, and what does the model say is
> driving that likelihood?

## Why this is a targeting problem, not a classification problem
The business doesn't need a yes/no prediction for every customer — it needs a
ranked list it can act on with a fixed budget (e.g., "we can afford to contact the
top 5,000 customers this month"). That reframes the success metric away from
accuracy/AUC and toward **precision@K and lift over baseline targeting**: of the top
K customers by predicted propensity, how many actually adopt, compared to what
random/naive targeting would achieve?

## Why this dataset
The Santander Product Recommendation dataset is real (anonymized) retail banking
data with monthly snapshots of product holdings and customer profile attributes —
it's one of the few public datasets that actually supports a "did this existing
customer add a new product" label, which is what a cross-sell propensity model
needs. It's not a synthetic or toy dataset, so the data quality issues (missingness,
inconsistent codes, new/departing customers) are realistic and worth discussing in
an interview.

## Scope and limitations (stated up front, not hidden)
- This is Spanish retail banking data (2015–2016). Customer behavior, product mix,
  and regulatory context don't directly generalize to any other bank or market —
  this project demonstrates *methodology*, not a plug-and-play model for a real
  employer's book of business.
- Any ROI or cost/value figures used in Phase 4 are **simulated assumptions** for
  illustrating the targeting framework, not measured or causal effects. The dataset
  has no experimental (treatment/control) structure, so no causal claim about
  "contacting a customer causes adoption" can be made from it — only association.
- The adoption label is defined mechanically from month-over-month flag changes; it
  doesn't distinguish a customer-initiated adoption from a bank-initiated one (e.g.,
  automatic product bundling), which is a caveat worth surfacing in the writeup.

## What "done" looks like
A model that ranks non-holders of Service A by adoption propensity, a plain-English
explanation of the top drivers (via SHAP), an identified high-propensity/under-served
segment, and a targeting simulation showing lift over naive targeting — all
documented so it reads as a coherent analysis a hiring manager could follow end to
end, including its limitations.

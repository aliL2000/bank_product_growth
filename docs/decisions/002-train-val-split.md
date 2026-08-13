# Decision Record: Train/val split design

## Title
Time-respecting train/val split: last 3 labeled months as validation, no gap month, period-based (not customer-holdout).

## Date
2026-08-13

## Context
Phase 2 needs a train/val split before any feature engineering or model
training can start. The dataset is a customer x month panel (13.6M rows,
~950K customers, 17 monthly snapshots), and the adoption label
(`data/processed/adoption_labels_tjcr.csv`) has 16 labeled months
(2015-02 through 2016-05; 2015-01 has no t-1 to compare against). Adoption
rate drifts down over time (~0.56–0.81% in 2015 down to ~0.42–0.48% by
early 2016, per-month table in the 2026-08-13 working log). A random
row-level split would leak information (a customer's future behavior
correlating with their past behavior within the same split), so the split
has to respect chronology.

## Decision
- **Validation = last 3 labeled months** (2016-03, 2016-04, 2016-05).
  Train = the other 13 labeled months (2015-02 through 2016-02).
- **No gap month** between train and val.
- **Split is by time period, not by customer** — the same `ncodpers` can
  (and will) appear in both train and val, at different months.
- Rows with `label_defined == False` (2015-01, and later gap rows for
  customers with no prior-month row) are dropped from the split entirely —
  they have no usable label.

## Why
- **3 months of val gives a real evaluation set**: ~2.77M rows, 12,749
  adoption events (0.46% rate) — enough positives to compute precision@K
  without it being dominated by noise, while still leaving 13 months
  (~9.91M rows, 56,369 events) for training.
- **No gap month needed**: each row is already point-in-time correct by
  construction — it's keyed by month *t*, uses only month *t-1* profile
  data (the leakage-safe join built in Phase 1), and the label reflects
  adoption by *t*. A row's own information never reaches past its own
  month, so there's no cross-boundary leakage a gap month would need to
  absorb.
- **Period split, not customer split, is the right question to ask**: the
  goal is "does a model trained on past months generalize to a future
  month" (the real deployment scenario — score existing customers going
  forward), not "does it generalize to never-before-seen customers." A
  customer-holdout split would test a different, less relevant question
  here.
- **Validating on the most recent months** matches deployment reality (the
  model would be scored against the future, not an arbitrary past slice)
  and stress-tests the model against the lower adoption rate observed in
  early 2016 rather than the higher rate in mid-2015.

## Alternatives considered
- **Random row-level split**: rejected — leaks within-customer
  autocorrelation across train/val.
- **Customer-level holdout split** (some customers entirely in val): would
  answer a different question (unseen-customer generalization) than the
  one this project cares about (future-month generalization for an
  existing customer base), so not used here.
- **2-month validation window**: considered as a way to keep more data in
  train; not chosen because 3 months' extra validation events (roughly
  4,100–4,400 more) meaningfully firms up precision@K estimates at little
  cost to train size (13 vs. 14 months).
- **Gap month between train and val**: considered as a generic
  time-series-split precaution, but rejected as unnecessary once the
  point-in-time construction of the label (t-1 features only) was
  confirmed to already prevent boundary leakage.

## Consequences / what this affects downstream
- `src/features/train_val_split.py` writes `data/processed/train_val_split.csv`
  (`ncodpers`, `fecha_dato`, `split`), gitignored like the other processed
  outputs — rerun the script if missing.
- Phase 2 feature engineering and model training should join features to
  this split file on (`ncodpers`, `fecha_dato`) rather than re-deriving the
  split.
- Any global aggregate features (e.g. mean-encodings) built in Phase 2 must
  be computed from train only and applied to val, not fit across both — the
  split being period-based makes this an easy mistake to make since val
  rows sit later in the same file, not in an obviously separate customer
  set.

# Decision Record: Eligibility filter on the modeling population

## Title
Restrict train/val split to eligible non-holders (`prev_flag == 0`) — drop
already-holder rows from the modeling population.

## Date
2026-09-11

## Context
`/audit` (2026-09-11) found that `train_val_split.py` kept every row with a
defined label, including customers who already held a credit card at t-1.
For those rows `adoption` is `False` by construction — they can't "adopt" a
product they already hold — not because they were offered the product and
declined. Checked the actual numbers: of 12,682,421 labeled rows, 570,732
(4.5%) are already-holders. Worse, the three Phase 2 feature-check
notebooks compute their headline correlation numbers (e.g. product_count's
~0.13, cited in `ROADMAP.md` as "the strongest signal found so far") over
the *uncorrected* train split, so this contamination was already shaping
which features look strongest.

## Decision
`train_val_split.py` now filters to `label_defined & (prev_flag == 0)`
before assigning the train/val split, instead of just `label_defined`. This
drops the split from 12,682,421 rows to 12,111,689 rows (the eligible
non-holder population Phase 1 already identified). Downstream feature files
(`features_tenure_activity.csv`, `features_product_count.csv`,
`features_demographics.csv`) are rebuilt against the corrected split.

## Why
- A propensity model should learn "who is likely to adopt if targeted,"
  not "who already has it." Mixing structurally-ineligible rows into the
  negative class teaches the model to (partly) predict pre-existing
  card ownership, which isn't the deployment question (targeting outreach
  only makes sense for non-holders in the first place).
- The eligibility population (12,111,689 rows) was already computed and
  reported in the Phase 1 adoption-label build (2026-08-02 working log
  entry) — this fix makes the split consistent with a number the project
  had already established as correct, rather than introducing a new
  definition.
- Filtering at the split stage (not the label stage) keeps
  `build_adoption_label.py` as a general-purpose label builder — the label
  itself (adoption = 0→1 transition) is still correctly defined for every
  row; eligibility is a *modeling population* choice, which belongs with
  the split.

## Alternatives considered
- **Filter inside each feature-build script instead of the split**:
  rejected — would need to be repeated identically in every feature script
  (and every future one), risking the same kind of drift the imputation
  train/val rule already warns about. Filtering once upstream means every
  downstream file inherits the correct population automatically.
- **Keep already-holders but add an `is_eligible` flag instead of
  dropping**: considered, since it would preserve the option to build a
  separate "upgrade/cross-hold" model later. Not chosen for now — no such
  model is planned, and keeping ineligible rows in the file makes it easy
  to forget the filter in a future script. Revisit if a future phase
  actually wants the already-holder population for a different question.

## Consequences / what this affects downstream
- `data/processed/train_val_split.csv` drops from 12,682,421 to 12,111,689
  rows once `train_val_split.py` is rerun.
- All three Phase 2 feature files must be rebuilt against the corrected
  split (they join on `ncodpers`/`fecha_dato` from `train_val_split.csv`).
- The three feature-check notebooks' correlation numbers need re-running
  post-fix; `ROADMAP.md`'s "strongest signal so far" claim should be
  re-verified rather than assumed unchanged.
- Baseline modeling (next roadmap step) now trains only on the corrected,
  eligible population by default, with no per-script filter needed.

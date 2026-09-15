# Concepts Log

Dated entries explaining non-trivial techniques used in this project, per
`CLAUDE.md`'s teaching requirement.

### 2026-07-28 — Chunked (out-of-core) CSV reading

**Concept**: Reading a CSV in fixed-size chunks with `pd.read_csv(..., chunksize=N)`
instead of loading the whole file into memory at once.

**Why here**: `train_ver2.csv` is 2.29 GB on disk with 13.6M rows. Extrapolating
from a 100k-row sample (110.6 MB in memory), a naive `pd.read_csv(TRAIN_PATH)`
would land around ~15 GB in memory — pandas' in-memory representation is
typically several times larger than the file on disk, mainly because of per-cell
overhead on object/string columns and the padding needed for missing values. That's
close enough to this machine's free RAM (~17 GB) that it risked slowing the
machine to a crawl or triggering swapping, just to compute simple things like row
counts and missing-value counts.

**How it works**: `pd.read_csv(path, chunksize=500_000)` returns an iterator
instead of a DataFrame. Each iteration reads and parses only the next 500k rows,
hands you that chunk as a normal DataFrame, and then the earlier chunk becomes
eligible for garbage collection once you're done with it. You accumulate whatever
summary statistics you need (row counts, per-column missing counts) across
chunks — `missing_total = chunk_missing if missing_total is None else
missing_total + chunk_missing` — so peak memory is bounded by one chunk's size,
not the whole file's.

**Watch out for**: Chunking only helps for computations that can be expressed as
a running accumulation (sums, counts, min/max). Anything that needs to see the
whole dataset at once — a global sort, a join across rows that might land in
different chunks, certain groupby aggregations — either needs a different
algorithm (e.g., an external sort, or a two-pass approach) or just needs enough
memory to hold the full result set. Also, chunk boundaries are arbitrary row
cuts, not aligned to any logical grouping (e.g., a customer's monthly rows could
be split across two chunks), so this approach only works for column-wise/row-wise
independent stats — not yet safe to use directly for the adoption-label join across
consecutive months, which will need its own memory-safe design in Phase 1.

### 2026-08-02 — Column pruning + dtype downcasting (an alternative to chunking)

**Concept**: Instead of streaming the whole file in chunks, load the full file in
one shot but only the columns you actually need (`usecols=`), with narrow dtypes
(`dtype={...}`) specified up front.

**Why here**: the adoption-label build only needs 3 of the 48 columns
(`fecha_dato`, `ncodpers`, `ind_tjcr_fin_ult1`). Loading all 13.6M rows with just
those 3, using `int32`/`int8` instead of pandas' default `int64`, used 273 MB —
comfortably in memory, versus the ~15 GB a full 48-column load would have needed.
Chunking (the previous entry) solves a different problem: it caps *peak* memory
when you must touch every column. Here the fix is cutting *what's loaded* in the
first place, which is simpler and doesn't force you to write accumulator logic.

**How it works**: `pd.read_csv` only allocates memory for the columns listed in
`usecols`, and honors the `dtype` dict at parse time rather than inferring (and
then having to downcast) after the fact. `int32` fits `ncodpers` (max ~1.4M, vs.
int64's default 8 bytes/value) and `int8` fits a 0/1 flag — both several times
smaller per cell than pandas' int64 default.

**Watch out for**: this only works when you know in advance exactly which
columns and value ranges you need — picking a dtype too narrow (e.g. `int8` for
a column that turns out to have values above 127) raises a `LossySetitemError` or
silently wraps around depending on the operation, so check the real min/max
first rather than guessing. It's also not a substitute for chunking when you
genuinely need many/most columns — at that point chunking (or both together) is
the right tool.

### 2026-08-02 — Merge-based lag join for panel (longitudinal) data

**Concept**: To get "this customer's value last month" for every row of a
dataset with repeated observations per entity over time (a customer x month
panel), join each row to the row for the *same entity* at *month - 1*, using an
explicit merge key — rather than a naive `groupby(...).shift(1)`.

**Why here**: the adoption label needs, for every (customer, month) row, whether
that same customer held a credit card in the *immediately preceding* calendar
month. `groupby("ncodpers")[flag].shift(1)` looks like the obvious tool, but it
shifts by *row position within the group*, not by actual elapsed time. If a
customer has a gap (present in Jan and Mar but not Feb — which happens: 7.1% of
rows here had no prior-month row at all), a positional shift would silently hand
you January's value and call it "last month," producing a wrong label with no
error.

**How it works**: build a lookup table keyed on `(ncodpers, month)` → flag value
(here, just the same dataframe renamed). For each row, compute `prev_month =
month - 1` (via pandas' `Period` arithmetic, so month-end/month-length issues are
handled correctly) and merge the lookup back in on `(ncodpers, prev_month)`. Rows
where no match exists (`prev_flag` is null) mean the customer's state one month
prior is genuinely unknown — a new customer, or a customer who churned out and
back — so the adoption label is left undefined (`pd.NA`) for those rows rather
than guessed at.

**Watch out for**: it's tempting to treat "no prior row" the same as "didn't have
the product" (i.e. impute 0), which would inflate the adoption-event count with
cases that are actually "customer just joined and immediately had it" rather than
genuine adoption. Here that's 964,888 rows (7.1% of the file) explicitly excluded
from the eligible population rather than silently mislabeled — worth stating
plainly in any writeup, since it's a modeling choice with a real effect on the
reported adoption rate.

### 2026-08-10 — Point-in-time correctness (avoiding label leakage in feature joins)

**Concept**: When attaching a customer attribute (age, income, activity flag,
etc.) to a labeled row, the attribute must be measured *before* the event
being predicted, not at or after it. "Leakage" is when a feature secretly
encodes information from the future relative to the prediction point, making
the model look far more accurate than it will ever be in production, where
that future information genuinely isn't available yet.

**Why here**: the EDA notebook (`notebooks/01_eda.ipynb`) needed to join each
adoption-label row (customer, month *t*) to that customer's profile
attributes to see how adoption varies by age, tenure, income, etc. The
tempting shortcut is to use the profile fields that live in the *same row* as
the label (i.e., month *t*'s own profile columns) — but month *t* is the
month the adoption already happened in. A customer's `ind_actividad_cliente`
(activity flag) or other attributes in month *t* could already reflect the
consequences of having just gotten the card, not their state beforehand. Any
pattern found that way risks being "the model learned that adopters look
different in the month they adopt" rather than "the model learned who is
about to adopt" — true but useless for the actual business goal of acting
*before* the event.

**How it works**: reuse the same merge-based lag-join technique from the
label build itself (`(ncodpers, month)` as an explicit key), but join the
label rows to the profile table at `month - 1` instead of `month`. This
guarantees every attribute used downstream (in this EDA, and later in Phase 2
features) was knowable at the point a targeting decision would actually have
to be made.

**Watch out for**: leakage is rarely this obvious in real projects — it's easy
to introduce it by accident through columns that look purely descriptive
("customer's current total balance") but are quietly computed using
data from after the prediction point, or through preprocessing done on the
full dataset before a time-based split (e.g., computing a mean or scaling
factor over all months, which lets information from future months leak into
earlier rows). The general check is: "could I have known this value at the
moment I'd need to act on the prediction?" — if not, it can't be a feature.

### 2026-08-13 — Time-respecting (period-based) train/val split

**Concept**: Splitting a panel dataset into train/validation by *time period*
rather than by row or by entity — every row from an earlier month goes to
train, every row from a later month goes to val, with no shuffling.

**Why here**: `train_test_split(..., shuffle=True)` (or any random split) would
put some of a customer's earlier-month rows in val and later-month rows in
train, or vice versa. Because consecutive months for the same customer are
highly correlated (tenure, activity, income barely change month to month), the
model would effectively get to see a smeared version of the answer during
training — inflating validation performance in a way that wouldn't hold up
once the model is scoring genuinely future, unseen months in production. Full
reasoning and the exact cutoff logged in
`docs/decisions/002-train-val-split.md`.

**How it works**: `src/features/train_val_split.py` tags every labeled row
(2015-02 through 2016-05) `train` if its month is before 2016-03, `val`
otherwise — the last 3 labeled months become validation (2.77M rows, 12,749
adoption events), the other 13 become train (9.91M rows, 56,369 events). No
random component at all; the split boundary is a single date. Note this is a
period split, not a customer split — the same `ncodpers` legitimately shows up
in both train and val (at different months), since the question being tested
is "does this generalize to future months," not "does this generalize to
unseen customers."

**Watch out for**: a period split only prevents *temporal* leakage — it does
nothing about leakage from aggregate statistics computed across the whole
dataset before splitting. Any global feature built in Phase 2 (mean-encodings,
overall averages, scalers) still has to be *fit* on train only and *applied*
to val, or the val rows contaminate the statistic used to score them. Also,
because the same customer appears in both splits, it's tempting to mistake
that for a bug (e.g. thinking there's "customer leakage") — it isn't, as long
as no single *row's* features reach past that row's own month.

### 2026-08-17 — Train-fit imputation with a missingness indicator flag

**Concept**: When filling missing values in a feature, (1) compute the fill
value (a median, mode, mean, etc.) using *only* the train split, and apply
that same fixed value to both train and val rows, and (2) keep a separate
boolean column recording *which* rows were originally missing, rather than
letting the filled value silently look like a real observation.

**Why here**: `src/features/build_features_tenure_activity.py` needed to
fill `antiguedad` (tenure) and `ind_actividad_cliente` (activity index) for
the ~0.16% of rows where they're missing (same shared data-quality issue
flagged in the Phase 1 missingness scan). Computing the median/mode across
train+val together would mean the imputed value for a train row is
influenced, even slightly, by val rows' values — a small but real instance of
the same leakage `docs/decisions/002-train-val-split.md` already warns about
for any "global" statistic. Separately, imputing without a flag would make a
row that's missing "look like" a row whose real tenure happens to equal the
median — throwing away the information that the value was unknown at all,
which can itself be predictive (e.g. missing profile fields cluster with a
specific data-entry issue, not randomly).

**How it works**: `df.loc[train_mask, col].median()` (or `.mode().iloc[0]`
for a categorical/binary column) computes the fill value from train rows
only; `df[col].fillna(value)` then applies that single fixed number to every
row, train and val alike — val rows are *scored* by it, never *involved* in
computing it. Before filling, `df[col].isna()` is saved off into its own
`{col}_missing` boolean column so a downstream model can still tell "this was
a 49-month tenure" apart from "this was unknown and got the fallback value of
49."

**Watch out for**: this pattern needs to be repeated for *every* imputed
feature in Phase 2 (income, channel, etc.) — it's easy to forget on a later
feature and accidentally compute a fill value across the full dataset out of
habit. Also, a median/mode fit on train can technically fall outside the
range seen in val (e.g. if val's true distribution has shifted, which the
EDA already showed for tenure/activity over time) — that's expected and
correct, not a bug to "fix" by refitting on val.

### 2026-09-11 — Aggregating multiple raw columns into one derived feature

**Concept**: Building a single engineered feature (`product_count_prev`) by
summing across many raw columns (23 of the 24 `ind_*_ult1` product flags),
rather than feeding each flag into the model individually.

**Why here**: Feeding 23 separate binary flags into a model is possible, but
each one alone is a weak, sparse signal (most customers hold 0-2 of any
given product). Collapsing them into a single count turns 23 sparse columns
into one dense, easily-interpreted number — "how engaged is this customer
with the bank overall" — and, as the Group 2 feature check notebook
(`notebooks/03_feature_check_group2.ipynb`) showed, that single number
carries the strongest signal found in the project so far (~0.13
point-biserial correlation with adoption, vs. ~0.05-0.08 for Group 1's
tenure/activity features): adoption rate climbs from ~0.07% at 0 other
products to ~4.3% at 6+, a ~60x range.

**How it works**: `df[product_cols].sum(axis=1)` adds across columns (not
rows) for each customer-month, producing one integer per row — same
point-in-time (t-1) join as every other Phase 2 feature, then a row-wise
`.sum(axis=1)` instead of any single-column transform. The target product
itself (`ind_tjcr_fin_ult1`) is excluded from the sum on purpose: since
eligibility for the label requires *not* holding it at t-1, including it in
the count would either always add 0 (for eligible rows) or trivially
determine the label for already-holder rows in the split — neither adds
real information, so it's left out to keep the feature about *other*
engagement.

**Watch out for**: aggregating away detail like this trades interpretability
of *which* product for a cleaner overall signal — you lose the ability to
say "holding a mortgage specifically predicts X" once it's folded into one
count. Also, a sum like this can end up correlated with other features built
the same way (tenure accumulates products over time too), which matters for
Phase 3 explainability — a strong individual correlation doesn't mean
independent predictive value once features are combined in a model.

### 2026-09-11 — Group-wise imputation

**Concept**: Filling missing values with a statistic computed *per category*
(e.g. per `segmento`) instead of one single constant for the whole dataset.

**Why here**: `renta` (income) is ~20% missing, and income genuinely varies
by customer segment — the train-only median is ~€89k for UNIVERSITARIO vs.
~€142k for TOP, a 1.6x spread. A single global median (~€102k) papers over
that difference, silently pulling every imputed UNIVERSITARIO row's income
up and every imputed TOP row's down. Since `segmento` is already being
built as a feature in this same group, grouping the imputation by it costs
nothing extra to compute.

**How it works**: `df.loc[train_mask].groupby("segmento")["renta"].median()`
computes one median per segment, using train rows only (same leakage rule
as every other imputation in this project). Each row then looks up its own
segment's median via `.map()`. Rows whose segment is itself missing (~1.4%)
have nothing to look up, so they fall back to the plain global train
median — a two-level fallback (group median, then global median) rather
than leaving those few rows unimputed.

**Watch out for**: this only helps when the grouping column is itself
reliable and mostly non-missing — grouping by a column that's 50% missing
just pushes half the problem into the fallback anyway. Also, more groups
means fewer rows per group; with a 3-category column like `segmento` each
group still has millions of rows, but a group-wise median computed on a
rare category (say, a few hundred rows) can be unstable — worth checking
group sizes before trusting a group's median.

### 2026-09-11 — Log-transforming a skewed numeric feature

**Concept**: Replacing a right-skewed numeric column with `log1p(x)`
(`log(1 + x)`, which handles zero cleanly) before feeding it to a model.

**Why here**: `renta` ranges from ~€1.2k to ~€29M, with the mean (~€135k)
well above the median (~€102k) — a small number of very high earners
stretch the distribution out. A plain logistic regression fits one linear
coefficient per feature, so a handful of €10M+ rows can dominate that
coefficient and drown out the meaningful variation in the €50k-200k range
where almost everyone actually falls. Confirmed empirically, not just in
theory: `renta_log`'s correlation with adoption (~0.022) came out 2.6x
`renta_imputed`'s (~0.008) in the Group 3 feature-check notebook.

**How it works**: `np.log1p(x)` compresses large values much more than
small ones (the gap between €1M and €2M shrinks a lot more than the gap
between €10k and €20k), which pulls extreme outliers back toward the bulk
of the distribution instead of letting them dominate. The `+1` inside
`log1p` (vs. plain `log`) just avoids `log(0)` being undefined, which
doesn't matter much here since no customer has exactly €0 income, but it's
a defensive habit worth keeping.

**Watch out for**: this transform matters for linear models (logistic
regression) but is close to irrelevant for tree-based models like LightGBM,
since trees split on thresholds and are invariant to any monotonic
transform of a feature — `renta_imputed` and `renta_log` would produce
nearly identical trees. Keeping both columns means each model gets the
version suited to it, rather than guessing which one baseline modeling will
prefer.

### 2026-09-11 — Eligibility / population definition in a propensity model

**Concept**: Before splitting into train/val or building features, restrict
the modeling population to rows where the outcome was actually *possible* —
here, customers who did **not** already hold a credit card at t-1. This is
a different check from label leakage (features/labels using future
information) — it's about whether a row belongs in the dataset at all.

**Why here**: `/audit` found that `train_val_split.py` was keeping every
row with a defined label, including 570,732 rows (4.5%) where the customer
already held a credit card at t-1. For those, `adoption` is `False` purely
because they already have the product, not because they were offered it
and declined — a structurally different kind of "no" than the one the
model is supposed to learn to predict. Worse, the three feature-check
notebooks were computing their correlation numbers over this uncorrected
population, so the contamination was already shaping which features looked
strongest.

**How it works**: `train_val_split.py` now loads `prev_flag` alongside
`label_defined` and filters to `label_defined & (prev_flag == 0)` before
assigning `train`/`val` — dropping the split from 12,682,421 to 12,111,689
rows (exactly the eligible-non-holder count Phase 1 had already computed
back on 2026-08-02). Filtering once at the split stage means every
downstream feature file inherits the correct population automatically,
rather than needing the same filter repeated in each feature script.
Full reasoning in `docs/decisions/003-eligibility-filter.md`.

**Watch out for**: after rebuilding the split and all three feature files
and re-running the sanity-check notebooks, the numbers moved — not just
noise. `product_count_prev`'s correlation with adoption rose from ~0.13 to
~0.163 (tenure/activity/demographics moved only slightly: ~0.05→0.059,
~0.08→0.083, age ~0.033→0.035). The contaminated already-holder rows were
*diluting* product_count's true signal (those rows have high product
counts but a label that's trivially `False`, weakening the correlation) —
a useful reminder that population contamination doesn't always inflate a
metric; it can just as easily mask a real effect. Feature ranking order
was unchanged, but the magnitude wasn't safe to assume.

### 2026-09-12 — Columnar file formats (Parquet vs. CSV)

**Concept**: Parquet is a binary, columnar file format for tabular data —
each column is stored contiguously with its own dtype metadata, rather than
CSV's row-by-row plain text where every value is just a string until
something parses it.

**Why here**: `/audit` flagged the five ~600MB+ CSV intermediates in
`data/processed/` ([csv-intermediate-files]) as an easy win. Beyond size,
CSV's lack of stored dtypes was already a real bug source — the pandas
`IndexError` on 2026-08-13 and the awkward `dtype={"adoption": "str"}`
workaround in `train_val_split.py` both existed only because a boolean
column written to CSV round-trips as the *text* `"True"`/`"False"`, not an
actual boolean, unless every dtype is redeclared by hand on read.

**How it works**: `df.to_parquet(path)` / `pd.read_parquet(path)` (via the
`pyarrow` engine) serialize each column with its real dtype — including
pandas-specific ones like nullable `boolean` and `Period[M]`, confirmed by a
round-trip test before migrating any real script. Nothing needs a `dtype=`
dict on read anymore. Migrating the five build scripts and four notebooks in
this project shrank `data/processed/` from ~2.9 GB to ~395 MB (about 7x),
mostly because columnar storage compresses far better than text when many
values in a column repeat (e.g. a mostly-0/1 flag column, or a `split`
column with only two distinct values).

**Watch out for**: Parquet isn't human-readable — you can't `head` it in a
text editor to eyeball a few rows the way you could a CSV; you need pandas
(or a tool like `parquet-tools`) even for a quick look. It also depends on
an engine library (`pyarrow` here) being installed, which CSV never needed.
Kept the raw Kaggle files (`train_ver2.csv`/`test_ver2.csv`) as CSV since
those are the original source data, not something this project generates —
only the five derived intermediates were migrated.

### 2026-09-12 — Unit tests and merge-safety assertions

**Concept**: A unit test calls one function with a small, hand-built input
and asserts the output matches a known-correct expectation — distinct from
this project's existing sanity-check notebooks, which look for *plausible*
signal on the real 12M-row data rather than an *exact* known answer on a
tiny synthetic one. A merge-safety assertion is a runtime `assert` placed
right after a join, checking an invariant that should always hold (e.g. "a
left join must not change the row count") so a violation fails loudly at
run time instead of silently producing a wrong file.

**Why here**: `/audit` called the adoption-label merge "the single point of
failure for the whole project" with zero automated checks
([no-tests-on-label-logic]) — before this, only a human eyeballing summary
stats would catch a broken merge, a flipped comparison, or a future edit
that reintroduces the eligibility-filter bug from
`docs/decisions/003-eligibility-filter.md`.

**How it works**: added `pytest` (`requirements.txt`, `pytest.ini` with
`pythonpath = src` so tests can `import features.build_adoption_label`
without needing `__init__.py` files) and a `tests/` directory with 12 tests
covering `build_label()`'s core scenarios (adoption, already-holder,
non-adoption, undefined label, a gap month) plus the split assignment and
each feature script's t-1 join. Separately, added an `assert len(merged) ==
len(input_df)` line directly inside `build_label()` and each feature
script's `attach_profile()`, right after the merge — this catches a
regression during a *real* run (e.g. if the raw file ever gains a
duplicate `(ncodpers, fecha_dato)` row), which a unit test on synthetic
data can't do since it only exercises hand-built cases.

**Watch out for**: unit tests validate *logic* on cases you thought to
write, not *signal* on real data — they don't replace the feature-check
notebooks, which check whether cleaned/imputed features still correlate
with adoption. Both are needed for different failure modes. Also, an
`assert` compiled out under Python's `-O` flag is a known footgun in
general, but not a concern here since these scripts are always run as
plain `python script.py`, never with `-O`.

### 2026-09-13 — Held-out test set (train/val/test, not just train/val)

**Concept**: A held-out test set is a third data bucket, disjoint from
train and val, that's used *once* — at the very end, only to report a
model's final performance — and never touched while choosing between
models or hyperparameters. Val stays the bucket you compare candidates on
as many times as needed; test is the number you're willing to stand behind.

**Why here**: the upcoming baseline step compares logistic regression vs.
LightGBM (and likely tunes LightGBM's hyperparameters) using val. If the
same val set were then quoted as "the model's performance" in
`reports/02_baseline_model.md`, that number would be optimistically biased
— repeatedly picking whatever scores best on a fixed val set means some of
that score reflects fitting val's specific quirks, not true generalization.
Flagged as open `/audit` finding [no-held-out-test-set] on 2026-09-11; this
project's numbers are also meant to eventually back verified resume
bullets (`docs/resume_bullets.md`), which raised the bar on rigor here.

**How it works**: `src/features/train_val_split.py` now assigns each
labeled, eligible row to one of three chronological buckets instead of two
— train (2015-02 to 2015-12, 11 months), val (2016-01 to 2016-02, 2
months), test (2016-03 to 2016-05, 3 months, unchanged from the old val
window). Same period-based logic as the original 2-way split (`
docs/decisions/002-train-val-split.md`): train on the past, validate on a
more recent slice, and now report on the most recent slice of all, matching
the real deployment question of "does this generalize to the future."
Model workflow going forward: fit on train, compare/tune on val, compute
the final reported metric on test exactly once. Full reasoning in
`docs/decisions/004-three-way-split.md`.

**Watch out for**: the discipline only works if test is genuinely never
looked at during model selection — checking test performance "just to see"
partway through modeling and then going back to tune further silently
turns test into a second val set. Also, since this split is period-based
(not customer-level), all three buckets share the same customers at
different months — same caveat as the original split: any train-only
statistic (imputation medians, mean-encodings) must be fit on train alone
and applied to val/test, never fit across buckets.

### 2026-09-13 (cont'd) — Pinned dependencies (`==`, not bare names)

**Concept**: `requirements.txt` listing bare package names (`pandas`, not
`pandas==3.0.3`) means `pip install -r requirements.txt` resolves whatever
the *latest available* version is *at install time* — a different day, a
different machine, or a different person running that command can silently
get different library versions than the ones this project's numbers were
actually produced with.

**Why here**: `/audit` found `scikit-learn`/`lightgbm`/`shap`/`streamlit`/
`seaborn` weren't installed at all in this environment despite being listed
- fixing that with `pip install -r requirements.txt` surfaced a second,
real problem: the resolved `numpy` jumped from 1.26.1 to 2.4.6 (a major
version), which broke `shap`'s `opencv-python` dependency (compiled against
numpy 1.x's ABI) until `opencv-python` was itself upgraded to a numpy-2-
compatible build. Pinning locks in the exact combination that's confirmed
to actually work together, so a future install doesn't silently redo this.

**How it works**: after confirming every package imports cleanly and
`pytest` passes, each line in `requirements.txt` was rewritten from a bare
name to `package==<installed version>` (e.g. `pandas==3.0.3`,
`numpy==2.4.6`), including `opencv-python==5.0.0.93` added explicitly even
though it's only an indirect dependency (via `shap`) - pinning it directly
prevents pip from re-resolving an old, numpy-2-incompatible version on a
future fresh install.

**Watch out for**: pinning freezes the *known-good* combination, not
necessarily the *best* one - a future intentional upgrade (e.g. a newer
LightGBM with a needed feature) still means manually bumping the pin and
re-verifying everything imports and tests pass, not just editing one line
and assuming it's fine.

### 2026-09-15 — Assembling a wide modeling table (`merge(..., validate=)`)

**Concept**: The four pieces built across Phase 2 (the eligible population +
split, the adoption label, and three feature files) each live in their own
file, keyed the same way: one row per (`ncodpers`, `fecha_dato`). Assembling
them into one "modeling table" is just a chain of left joins on that shared
key - no new logic, just combining what already exists. Pandas'
`merge(..., validate="one_to_one")` adds a built-in check that neither side
of a join has a duplicate key, instead of relying only on a manual
`assert len(merged) == len(before)` (used in the earlier feature scripts).

**Why here**: a baseline model needs one flat table - id columns, the
target, and every feature column - not four files a model has to be
manually stitched together from each time. Doing the stitching once here,
rather than inside the modeling script, keeps that script focused on
modeling instead of data plumbing.

**How it works**: `src/features/build_modeling_table.py` starts from
`train_val_split.parquet` (the eligible, labeled population with its
train/val/test tag) and left-joins in the label, then each feature file in
turn, all on `(ncodpers, fecha_dato)`. `validate="one_to_one"` makes pandas
raise immediately if either side of a join turns out to have a repeated
key - which would silently multiply rows (a "fan-out") rather than just
adding columns. The row-count assert stays too, since `validate` only
checks for duplicate *keys*, not that every row on the left found a
match on the right (a row with no match still passes `validate`, it just
gets `NaN`). Output: `data/processed/modeling_table.parquet`, 12,111,689
rows x 22 columns - one row per eligible labeled customer-month, with
`split`, `adoption`, and every Phase 2 feature.

**Watch out for**: `validate="one_to_one"` only proves the join was safe
given the *keys* it saw - it can't catch a case where the keys are unique
but wrong (e.g. accidentally joining month t instead of month t-1, which
each feature script's own point-in-time logic is responsible for getting
right *before* this assembly step ever runs). Assembly-time validation and
per-feature point-in-time correctness are two different failure modes,
and this step only guards the first one.

### 2026-09-15 (cont'd) — Per-bin lift table + a squared term for a non-monotonic feature

**Concept**: Pearson correlation measures how well a *straight line* fits a
relationship. It's the wrong tool when a feature's true relationship with
the target rises then falls (or vice versa), because the positive
deviations on one side and negative deviations on the other partially
cancel out in the calculation - the number comes out small even if the
underlying pattern is strong. A per-bin lift table (bucket the feature,
compute the target rate in each bucket, compare to the overall rate) makes
no assumption about shape and reveals the true pattern directly. Once a
non-monotonic pattern is confirmed, a linear model (logistic regression)
still can't use it from the raw feature alone - the standard fix is adding
a squared term, so the model can fit a parabola instead of a straight line.

**Why here**: `docs/audit_log.md`'s
[correlation-yardstick-vs-nonmonotonic-feature] finding flagged that
`age_years`'s Pearson correlation (0.0356, "weak") was being used to judge
its usefulness, despite Phase 1 EDA already noting adoption peaks in
middle age. The upcoming baseline compares logistic regression against
LightGBM - if age truly matters and LR can't see it, that would make LR
look artificially worse for a reason that has nothing to do with the
algorithm, only with how the feature is represented.

**How it works**: computed a lift table on the train split (12
age buckets, adoption rate per bucket vs. the 0.63% overall rate) — result:
lift ranges from ~0.04x (20-25) up to ~2.04x (45-50) back down to ~0.29x
(80+), roughly a 50x range that Pearson's "weak" 0.0356 badly understated.
Rank correlation (Spearman) was considered but rejected as *also* wrong
here - it only handles monotonic-but-nonlinear relationships, not a curve
that rises and falls, so it would have made the same mistake as Pearson in
a different guise. Fixed by adding `age_years_sq` to
`build_features_demographics.py`: age is centered on the *train-only* mean
before squaring (not squared raw), which keeps `age_years` and
`age_years_sq` less correlated with each other than squaring raw age would
- logistic regression can then combine both terms to approximate the
observed parabola shape. LightGBM needs no such help; tree splits find
non-monotonic patterns on the raw feature automatically, so this addition
is purely to keep the LR baseline from being handicapped by something
already known about the data.

**Watch out for**: a squared term only fits a *symmetric* parabola: the
observed shape isn't perfectly symmetric (the decline is gentler and
longer on the older side than the rise is on the younger side), so this is
an approximation, not a perfect fit - if LR's results still look
age-blind after this, the next step up would be age buckets (one-hot
bins) instead of a parametric curve, which can fit any shape at the cost
of more columns and no smooth extrapolation between bins.

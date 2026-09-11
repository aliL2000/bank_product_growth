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

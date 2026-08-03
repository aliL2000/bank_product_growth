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

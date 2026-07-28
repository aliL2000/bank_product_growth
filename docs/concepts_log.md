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

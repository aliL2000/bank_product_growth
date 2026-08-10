# CLAUDE.md — instructions for Claude Code in this repo

## Session start protocol (do this before proposing any work)
This is a long-running project worked on in short daily-ish sessions, often as a
fresh Claude Code session with no memory of prior conversations. Before proposing
or starting any work in a new session:

1. Read `ROADMAP.md` in full — the checkboxes show phase progress, and the
   **Working Log** (dated, newest at the bottom) has the real narrative: what was
   done, what was found, and each entry's final "Next:" line is the intended
   starting point for the following session.
2. Skim `docs/decisions/` (filenames are numbered — read the highest-numbered
   ones first) for any settled decisions that constrain what you should suggest
   (e.g. don't re-litigate which product is "Service A" — check first).
3. Skim `docs/concepts_log.md`'s most recent entries so explanations stay
   consistent with what's already been taught, instead of re-explaining a concept
   from scratch or contradicting an earlier explanation.
4. Sanity-check that `data/raw/train_ver2.csv` and `test_ver2.csv` are still
   present before assuming any data-dependent step can run — they're gitignored,
   so a fresh clone or a different machine won't have them.
5. Only after that, propose the next concrete step — don't assume the person
   wants you to auto-continue through multiple ROADMAP phases in one sitting
   (see "Incremental workflow" below).

## Teaching requirement (non-negotiable for this project)
This project exists partly so I (Adam) learn the concepts, not just get working code.
Every session, for every non-trivial thing you implement:

1. Before writing code for a new concept/technique, briefly explain it first —
   what it is, why it's the right tool here, what the alternative approaches were
   and why you didn't pick them.
2. After implementing, append a dated entry to `docs/concepts_log.md` with:
   - **Concept**: name it
   - **Why here**: what problem in this project it solves
   - **How it works**: plain-English explanation, no hand-waving
   - **Watch out for**: common misuse / pitfall
3. Don't just say "I used LightGBM" — explain what gradient boosting is doing,
   why it beats logistic regression on this kind of tabular data, and what its
   failure modes are. Same standard for every technique: time-based splitting,
   precision@K, SHAP, whatever comes up.
4. Keep explanations proportional — a one-line concept doesn't need five paragraphs,
   but never skip the explanation entirely just because the code was quick to write.

## Incremental workflow
- Small real commits, one working session at a time — no giant batch implementations.
- At the end of each session, update `ROADMAP.md`'s working log with what was done
  and what concept was taught.
- If a session's main output is a concept explanation with no code changes, that's
  a valid session — don't force code just to have a diff.
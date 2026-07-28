# CLAUDE.md — instructions for Claude Code in this repo

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
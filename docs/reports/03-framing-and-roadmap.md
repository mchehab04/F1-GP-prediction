# 03 — Framing the project and writing the roadmap

**Date:** 2026-09-13 · **Phase:** Phase 0 (partly done)

**In short:** I wrote a 12-phase roadmap that runs from framing through to presenting the results. I also made the two decisions you can't start without: what I'm predicting, and where the data lives. The rest of Phase 0 (git, README, baseline, metrics) is still open.

## What I did

- Wrote [ROADMAP.md](../../ROADMAP.md): Phase 0 (framing) → 1 (fetching) → 2 (cleaning) → 3 (SQL) → 4 (EDA) → 5 (statistics) → 6 (causal) → 7 (features) → 8 (modeling) → 9 (evaluation) → 10 (deployment) → 11 (communication). Each phase ends with a **Done when** line, so I know when to move on.
- Decided the question and the storage (below).

## Main decisions

**The question:** *After qualifying, predict each driver's finishing position for the Grand Prix.*

- I picked position over "who wins" or "podium yes/no" because podium and points probabilities can be derived from a position model later. The reverse isn't true.
- "After qualifying" is the **decision point**. Every feature has to be something I could have known at that moment. That rules out race-day weather, the race's own lap data, and anything else from the race itself. Most leakage comes from breaking this rule, so it's worth fixing early.

**Storage:** DuckDB + Parquet.

- DuckDB gives real SQL (window functions, CTEs, views) from a single file, with no server to run.
- It replaces the Postgres setup from the 2025 scripts, whose database no longer exists anyway ([01](01-starting-point-2025-ingest-scripts.md)).

Both are logged in [decisions.md](../decisions.md).

## Why this matters

The decision point turns "don't leak" into a yes/no test I can apply to every feature in Phase 7. Without it, "is this feature allowed?" gets argued case by case.

## Still open in Phase 0

| Item | Status |
|---|---|
| Decision point written as a rule ("after qualifying, before lights out") | Implied by the question, not formally written yet |
| 5–8 analytics questions a stakeholder would ask | Not started |
| Baseline ("finish = grid position") and metrics (MAE, Spearman, Brier) | Not started |
| Who the audience is | Not started |
| `git init`, `.gitignore`, `requirements.txt`, folder layout | Not started. **The project isn't under git yet.** |
| `docs/decisions.md` | Started with this batch of reports |

## Risks

- I started building the database ([04](04-first-database-fastf1-duckdb.md)) before Phase 0 was done. That's fine for learning, but without git, the changes to `create_db.py` over the last two days have no history. If a change breaks something, there's nothing to diff against.

## Files touched

[ROADMAP.md](../../ROADMAP.md) (new), [docs/decisions.md](../decisions.md)

## Next step

Build a first database from FastF1 → [04](04-first-database-fastf1-duckdb.md).

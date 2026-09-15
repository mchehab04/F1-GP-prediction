# 01 — Starting point: the 2025 ingest scripts

**Date:** 2025-09-06 → 2025-09-13 (from file dates) · **Phase:** before Phase 0

**In short:** Before this project had a plan, I wrote five scripts that pulled F1 data from two sources into a Postgres database. That database no longer exists. What's left on disk is a large FastF1 cache and a folder of raw OpenF1 files, and both turned out to be useful. The scripts also had bugs I didn't notice until I audited them a year later (see [02](02-data-audit.md)).

## What I did

| Script | Source | What it does |
|---|---|---|
| `ingest/fastf1_fetch.py` | FastF1 | Backfills **laps and weather** for 2021–2022, every session. Caps sessions per run (24 by default) to stay under FastF1's ~500 calls/hour. |
| `ingest/openf1_fetch.py` | OpenF1 API | For every 2023–2024 session: fetches sessions, drivers, starting grid, and results. Saves each response as a raw JSONL file, then writes it to Postgres. |
| `ingest/openf1_load_from_jsonl.py` | Local JSONL | Reloads those raw files into Postgres without calling the API again. |
| `ingest/openf1_meetings_backfill.py` | OpenF1 API | Fills a `meetings` table (one row per race weekend). |
| `ingest/openf1_results_grid_backfill.py` | OpenF1 API | A second pass over results and starting grid. |

What survived on disk:

- `fastf1_cache/`: ~570 MB covering 2021–2022, 44 events, every session. No car telemetry (the script ran with `telemetry=False`).
- `ingest/data/raw/openf1/`: 2023–2024, 48 meetings, 236 sessions. Contains sessions, drivers, results, and grid. No laps, stints, or weather.

## What I learned

- **Saving the raw responses was the right call.** Because the OpenF1 JSONL files exist, I can rebuild from them without touching the API. It's the one habit from this round I'd keep as-is.
- **Caching FastF1 paid off.** The new database script ([04](04-first-database-fastf1-duckdb.md)) reuses this cache, and one race in it can no longer be downloaded at all.
- **Every script invented its own schema.** Three scripts define the same `session_result` table three different ways. Nobody owned the table definition.
- **The database is gone, and the files survived.** All five scripts wrote to Postgres through `DATABASE_URL` in a `.env` file. That database doesn't exist anymore, so the only data left from this round is what the scripts also saved to disk. That's a good argument for always keeping a raw copy outside the database.

## Why this matters

The two sources don't overlap. FastF1 covers 2021–22 with laps and weather, and OpenF1 covers 2023–24 with results and grid. So I couldn't build even one feature across all four seasons from what I had, and that shaped every decision after this.

## Files touched

`ingest/*.py`, `fastf1_cache/`, `ingest/data/raw/openf1/`

## Next step

Audit what's actually on disk before building anything new → [02](02-data-audit.md).

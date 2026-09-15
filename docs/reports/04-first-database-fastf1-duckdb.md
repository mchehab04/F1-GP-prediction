# 04 — Building the first database (FastF1 → DuckDB)

**Date:** 2026-09-14 → 2026-09-15 · **Phase:** Phase 1 (first slice)

**In short:** [python/create_db.py](../../python/create_db.py) pulls the calendar, qualifying, race, and practice results for 2022–2026 from FastF1 into one file, `data/f1_db.duckdb`. You can stop it and rerun it at any time, and it picks up where it left off. That matters because FastF1 allows only ~500 calls an hour. A second script, [python/sql_ui.py](../../python/sql_ui.py), opens the database in a browser SQL editor.

## What I built

| Table | One row per | Main columns | Where it comes from |
|---|---|---|---|
| `races` | year, round | event name, location, country, `sprint_included` | FastF1 event schedule, testing excluded |
| `quali_results` | year, round, driver | position, `q1` / `q2` / `q3` in seconds | Qualifying session results |
| `race_results` | year, round, driver | position, `grid_position`, team, `status`, `classified_position`, points, laps | Race session results |
| `practice_results` | year, round, session, driver | position, `best_lap` in seconds | Worked out from lap data (see below) |

Every table has a primary key, so a duplicate row causes an error instead of slipping in. That's the exact problem [02](02-data-audit.md) found in the old OpenF1 files.

## How it works (the parts worth remembering)

- **It can resume.** Before fetching, each loader checks what's already saved and skips it. If I hit the rate limit or stop the script, rerunning continues from where it stopped.
- **Future sessions are skipped.** Anything with a date after now isn't fetched.
- **Failed downloads aren't saved as empty.** When a download fails, FastF1 only logs a warning and hands back empty results. The loaders check for that (all positions empty, or no lap data) and skip the session so a later run retries it. Without this check, a network blip would store a race with no results, and the resume logic would then treat it as done.
- **Practice has no official results in FastF1.** Its `Position` column is always empty. So I rank drivers by their best lap among laps flagged `IsPersonalBest`, which leaves out laps deleted for track limits.
- **Sprint weekends have fewer practice sessions.** From 2023, a sprint weekend has only FP1 (in 2022 it also had FP2). The loader treats "this session doesn't exist" as a skip, not an error.
- **The 2025 cache is reused.** `fastf1_cache/` from [01](01-starting-point-2025-ingest-scripts.md) saves re-downloading 2021–22 sessions.
- **SQL UI quirk.** `sql_ui.py` starts DuckDB's browser editor at `http://localhost:4213`. It attaches the F1 file read-only to an in-memory database. Opening the file directly with `read_only=True` breaks the UI, because the UI needs to create its own `_duckdb_ui` catalog.

## Where the data stands (2026-09-15)

| | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|
| Rounds in calendar | 22 | 22 | 24 | 24 | 23 |
| Sprint weekends | 3 | 6 | 6 | 6 | 6 |
| Rounds with qualifying | 22 | 22 | 24 | 24 | 14 |
| Rounds with race results | 22 | 22 | 24 | 24 | 14 |
| Rounds with FP1 | 22 | 22 | 24 | 24 | 14 |
| Drivers per race | 20 | 20 | 19–20 | 19–20 | 22 |

- Rows: 2,147 qualifying, 2,146 race, 5,338 practice. All three tables cover the same 106 rounds, which is every race held so far. 2026 rounds 15–23 haven't happened yet.
- Three races failed to download at first (2023 R12, 2023 R20, 2024 R3). Once the race loader got the same resume logic as the others, they were filled in. `race_results` was then dropped and rebuilt with more columns (grid position, team, status, classified position, points, laps).
- Quick sanity check: every race has exactly one winner.

## First look at `race_results`: encoding quirks for Phase 2

The new columns work, but the values aren't coded consistently between seasons:

| Quirk | Example | Why it matters |
|---|---|---|
| Lapped cars are written differently by season | 2022 uses "+1 Lap" (87 rows). 2023+ uses "Lapped" (398 rows). | The same outcome has two labels |
| Retirement causes only exist for 2022 | 2022 says "Engine", "Accident", etc. 2023+ mostly just says "Retired". | A DNF-cause feature would only work for one season |
| Disqualifications are coded two ways | 10 rows have status "Disqualified", but only 7 have `classified_position = 'D'`. The other 3 (2023 R18 HAM and LEC, 2024 R14 RUS) show a number. | Filtering on `'D'` misses 3 of the 10. **Use `status` for DSQ.** |
| Pit-lane starts are grid 0 | 13 rows | "Grid 0" would read as better than pole unless it's recoded |
| Withdrawn drivers have no position or grid | 2022 R2 MSC, 2023 R15 STR | These are the only nulls in `position` / `grid_position` |
| "W" covers two different things | 16 "Did not start" + 3 "Withdrew" | DNS and withdrawal need separate codes |

This is the "define result encoding" item in Phase 2, and now there's real data to base the rule on.

## Things that bit me, or could later

- **2022 Imola now returns HTTP 403** from F1's servers. It only exists in my local cache, so deleting `fastf1_cache/` would lose it for good. The cache stays (see [decisions.md](../decisions.md)).
- **`CREATE TABLE IF NOT EXISTS` doesn't update an existing table.** Adding columns in the code doesn't add them to the database file. The old table has to be dropped (or `ALTER`ed) and refilled, and the first sign of the mismatch is an insert error.
- **Practice "position" isn't official.** It's my own ranking by best valid lap, and a driver with no valid lap is missing from that session. That's fine for pace features, but it shouldn't be presented as the official classification.
- **No raw layer or fetch manifest yet.** The script writes straight from the API into the final tables. Phase 1's "Done when" asks for a rebuildable `data/raw/` plus a manifest of what was fetched. The cache covers part of that, but not the manifest.
- **Only half the storage decision is in use.** Everything is in DuckDB so far and nothing is in Parquet.
- **Seasons are 2022–2026, not 2018+ as the roadmap suggested.** That was deliberate: 2022 started the current regulation era, so older seasons would mix in cars built to different rules (see [decisions.md](../decisions.md)). But 2026 is another regulation reset, so the data is really two eras, and a model trained on 2022–25 should be expected to struggle early in 2026.
- **Not under git** (see [03](03-framing-and-roadmap.md)).

## Files touched

[python/create_db.py](../../python/create_db.py) (new), [python/sql_ui.py](../../python/sql_ui.py) (new), `data/f1_db.duckdb` (new)

## Next step

1. `git init` with a `.gitignore` for `fastf1_cache/`, `data/`, and `venv/`.
2. Finish Phase 0: a README with the question, decision point, baseline, and metrics.
3. Keep the encoding quirks above for Phase 2's result-encoding rule.

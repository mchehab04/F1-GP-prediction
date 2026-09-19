# Decision log

Append-only. If a later decision reverses one of these, it gets a new entry that points back to the old one. The old entry stays as it is.

---

## 2026-09-13 — Predict finishing position, after qualifying

- **Context:** Phase 0 needs one primary question before any data work.
- **Decision:** *After qualifying, predict each driver's finishing position for the Grand Prix.*
- **Why:** Podium and points probabilities can be derived from a position model later, but not the other way round. "After qualifying" fixes the decision point: every feature must be knowable at that moment.
- **Alternatives:** Predicting the winner only, or podium yes/no as the main target.
- **Follow-up:** Write the decision point formally as a rule ("after qualifying, before lights out") in the README. Report: [03](reports/03-framing-and-roadmap.md).

## 2026-09-13 — DuckDB + Parquet instead of Postgres

- **Context:** The 2025 scripts wrote to a Postgres database that no longer exists.
- **Decision:** Store data in DuckDB, with Parquet files for the data layers.
- **Why:** Real SQL without running a server. One file that's easy to rebuild.
- **Alternatives:** Keep Postgres, as the old scripts expect.
- **Follow-up:** Parquet isn't used yet, only DuckDB. Report: [03](reports/03-framing-and-roadmap.md).

## 2026-09-13 — FastF1 as the main source for every season

- **Context:** The existing FastF1 (2021–22) and OpenF1 (2023–24) data don't overlap in seasons or content ([02](reports/02-data-audit.md)).
- **Decision:** FastF1 for every season. Jolpica for long history and stable IDs. OpenF1 for 2023+ extras and cross-checking. Keep the old OpenF1 JSONL files as Phase 2 cleaning practice.
- **Why:** One API and one schema, with laps and results for every season. Harmonizing two different sources across four seasons would cost more than refetching.
- **Alternatives:** Patch the two existing datasets together.
- **Follow-up:** Jolpica and the extra OpenF1 endpoints haven't been fetched yet.

## 2026-09-14 — Database covers 2022–2026 only

- **Context:** The roadmap suggested fetching 2018 → present.
- **Decision:** `create_db.py` fetches 2022 onwards.
- **Why:** 2022 started the current regulation era (ground-effect cars). Earlier seasons were built to different rules, so their results say less about today's cars.
- **Alternatives:** 2018+ as in the roadmap, which would give more races but mix in cars built to older rules.
- **Follow-up:** 2026 is another regulation reset (new power units, a new team), so the data is really two eras: 2022–25 and 2026. The roadmap's Phase 9 already plans to evaluate 2026 separately. Report: [04](reports/04-first-database-fastf1-duckdb.md).

## 2026-09-14 — Practice "results" are ranked by best valid lap

- **Context:** FastF1 has no official practice classification: `Position` is always empty for FP1–FP3.
- **Decision:** Rank drivers by their fastest lap among laps flagged `IsPersonalBest`, which excludes laps deleted for track limits.
- **Why:** It's the closest match to the official timing sheet available from lap data.
- **Alternatives:** Use the fastest lap regardless of deletion (would count laps the stewards threw out), or skip practice entirely (it's the main pace signal before qualifying).
- **Follow-up:** A driver with no valid lap in a session is missing from that session. Treat this as a pace feature, not an official result. Report: [04](reports/04-first-database-fastf1-duckdb.md).

## 2026-09-15 — Keep `fastf1_cache/`

- **Context:** 2022 Imola now returns HTTP 403 from F1's servers.
- **Decision:** Never delete `fastf1_cache/`. It's the only copy of that race.
- **Why:** The data can't be downloaded again.
- **Alternatives:** Treat the cache as disposable and refetch (no longer possible for Imola 2022).
- **Follow-up:** Keep it out of git (it's ~570 MB+) but back it up somewhere. Report: [04](reports/04-first-database-fastf1-duckdb.md).

## 2026-09-16 — Separate `drivers` table for team moves and driver numbers

- **Context:** Drivers change teams mid-season (Lawson/Tsunoda in 2025) and numbers change across years (Verstappen #1 vs #3).
- **Decision:** Add a `drivers` table with primary key `(year, driver, team_name)`.
- **Why:** Keeps driver metadata normalized and avoids joins on unstable team names across seasons.
- **Alternatives:** Rely solely on `race_results.team_name`.
- **Follow-up:** Report: [05](reports/05-first-eda-and-sql-exports.md).

## 2026-09-16 — Standardize `classified_position` encoding

- **Context:** Raw FastF1 `race_results` has inconsistent strings for lapped cars, classifies 90%-distance crashers with finishing numbers, and splits DSQs between 'D' and numeric positions.
- **Decision:** Standardize `classified_position` into: numerical finishing position (`1`–`20`) for finished/lapped cars, `'R'` for all mechanical/incident retirements, `'D'` for disqualifications, and `'W'` for DNS/withdrawn.
- **Why:** Clean, mutually exclusive outcome categories are required for race completion analysis and modeling.
- **Alternatives:** Leave raw FastF1 strings and filter in every individual SQL query.
- **Follow-up:** Managed via `python/clean_data.py`. Report: [06](reports/06-cleaning-race-results.md).

## 2026-09-19 — Impute `NULL` position and grid_position for withdrawn drivers to 20

- **Context:** Two rows in `race_results` had `NULL` for both `position` and `grid_position`: MSC (2022 R2) and STR (2023 R15). Both withdrew prior to race start after severe qualifying accidents.
- **Decision:** Set `position = 20` and `grid_position = 20` for both.
- **Why:** In both races, only 19 cars started, occupying grid slots 1–19, leaving slot 20 completely vacant. Setting Schumacher's grid to his qualifying position (14) would create a duplicate grid slot with Ricciardo (who moved to 14 after a penalty and grid collapse). Setting both to 20 eliminates all nulls, avoids grid collisions, and matches how all other DNS entries are encoded in FastF1.
- **Alternatives:** Keep as `NULL` (would require null-handling in downstream models) or set Schumacher's grid to 14 (causes duplicate grid slots).
- **Follow-up:** Managed via `python/clean_data.py`. Report: [06](reports/06-cleaning-race-results.md).

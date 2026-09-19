# Project index

**Current phase:** Phase 1 database is built, Phase 2 data cleaning is in progress, and Phase 3 EDA queries and exports are underway. See [ROADMAP.md](../ROADMAP.md) for the full checklist.

## Reports

| # | Report | What it covers | Date | Phase |
|---|---|---|---|---|
| 01 | [Starting point: the 2025 ingest scripts](reports/01-starting-point-2025-ingest-scripts.md) | What the old scripts fetched, what survived on disk, and what they got wrong | 2025-09 | Before Phase 0 |
| 02 | [Auditing the data I already had](reports/02-data-audit.md) | Whether the old datasets can be combined, seven data-quality problems, and the switch to FastF1 | 2026-09-13 | Before Phase 0 |
| 03 | [Framing the project and writing the roadmap](reports/03-framing-and-roadmap.md) | The prediction question, the decision point, the storage choice, and what's left in Phase 0 | 2026-09-13 | Phase 0 |
| 04 | [Building the first database](reports/04-first-database-fastf1-duckdb.md) | `create_db.py`, the initial four tables, how resuming works, current coverage, and race-result encoding quirks | 2026-09-14 → 15 | Phase 1 |
| 05 | [First EDA queries and SQL exports](reports/05-first-eda-and-sql-exports.md) | `drivers` table addition, SQL EDA queries in `sql/eda/`, `data/exports/` CSVs via DuckDB `COPY`, and teammate gap observations | 2026-09-16 | Phase 3 |
| 06 | [Cleaning race results (`classified_position`)](reports/06-cleaning-race-results.md) | `clean_data.py`, standardizing finishes (`1`–`20`), retirements (`R`), disqualifications (`D`), and withdrawals (`W`), plus DuckDB Windows file locking | 2026-09-16 | Phase 2 |

## Other docs

- [decisions.md](decisions.md): the decision log, append-only
- [ROADMAP.md](../ROADMAP.md): phases 0–11 with "Done when" criteria

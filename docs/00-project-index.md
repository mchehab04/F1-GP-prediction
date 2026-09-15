# Project index

**Current phase:** Phase 0 (framing) is partly done, and a first slice of Phase 1 (FastF1 → DuckDB) is built. See [ROADMAP.md](../ROADMAP.md) for the full checklist.

## Reports

| # | Report | What it covers | Date | Phase |
|---|---|---|---|---|
| 01 | [Starting point: the 2025 ingest scripts](reports/01-starting-point-2025-ingest-scripts.md) | What the old scripts fetched, what survived on disk, and what they got wrong | 2025-09 | Before Phase 0 |
| 02 | [Auditing the data I already had](reports/02-data-audit.md) | Whether the old datasets can be combined, seven data-quality problems, and the switch to FastF1 | 2026-09-13 | Before Phase 0 |
| 03 | [Framing the project and writing the roadmap](reports/03-framing-and-roadmap.md) | The prediction question, the decision point, the storage choice, and what's left in Phase 0 | 2026-09-13 | Phase 0 |
| 04 | [Building the first database](reports/04-first-database-fastf1-duckdb.md) | `create_db.py`, the four tables, how resuming works, current coverage, race-result encoding quirks, and what could bite later | 2026-09-14 → 15 | Phase 1 |

## Other docs

- [decisions.md](decisions.md): the decision log, append-only
- [ROADMAP.md](../ROADMAP.md): phases 0–11 with "Done when" criteria

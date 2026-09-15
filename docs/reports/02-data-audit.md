# 02 — Auditing the data I already had

**Date:** 2026-09-13 · **Phase:** before Phase 0

**In short:** I went through the 2025 data file by file. The two datasets can be combined, but only after a lot of harmonizing. I also found seven data-quality problems in the OpenF1 files, and one of them silently deletes every qualifying lap time. My conclusion was to rebuild on FastF1 for every season and keep the old OpenF1 files as cleaning practice.

## What I did

I opened the FastF1 cache and every raw OpenF1 file, counted rows, and compared what was stored with what the scripts claimed to store. The full write-up is the "Existing data audit" section of [ROADMAP.md](../../ROADMAP.md).

## Can the two datasets be used together?

Yes, but not in the way I first expected:

1. **The seasons don't overlap** (2021–22 vs 2023–24). Combining them means stacking seasons on top of each other, not joining rows.
2. **The content doesn't overlap either.** One has laps and weather, the other has results and grid.
3. **The keys differ.** FastF1 rows use a made-up key (`year*10000 + round*10 + code`), while OpenF1 uses its own `session_key` (e.g. `7953`). I'll need one shared key: `(season, round, session_type, driver)`.
4. **Car number is not a driver ID.** Verstappen is #33 in 2021 and #1 from 2022. The 3-letter code (`VER`) is safer.
5. **Team names change.** AlphaTauri became RB, and Alfa Romeo became Sauber and then Audi. I'll need a lineage table.

## Data-quality problems found

| Problem | What goes wrong | Cause |
|---|---|---|
| 2023 sessions stored **5×** (565 rows, 113 unique). Drivers and results are duplicated too. | Every count is inflated | `dump_jsonl` opens files in append mode, so each rerun added another copy |
| Pre-season testing labelled "Practice 1/2/3" | Fake practice sessions in the data | Not filtered out by meeting |
| Qualifying `duration` / `gap_to_leader` are lists `[Q1, Q2, Q3]` | `pd.to_numeric` turns them into NaN, so **all qualifying times disappear with no error** | The loader assumed single values |
| Script reads `status`, `time`, `penalty_text` | Those columns are completely empty | The fields don't exist in the API. The real ones are `dnf`, `dns`, `dsq`, `duration`, `gap_to_leader`. |
| 126 results with no `position` | DNF/DNS/DSQ drivers have no encoding | No rule decided yet |
| "Sprint Shootout" (2023) vs "Sprint Qualifying" (2024) | Same session type under two names | Renamed between seasons |
| Three scripts, three schemas for the same tables | Which one is right depends on which script ran last | No single owner of the schema |

## Why this matters

Most of these would have gone straight into a model without anything complaining. The qualifying one worries me most: nothing crashes, the times just aren't there. That's the reason Phase 2 has "write validation checks as code", because I wouldn't have caught these by eye.

## What I decided

- **FastF1 is the main source for every season.** One API and one schema, with laps and results included.
- **Jolpica** (the successor to Ergast) for long history back to 1950 and for stable driver/team/circuit IDs.
- **OpenF1** for 2023+ extras, and as an independent source to cross-check FastF1 against.
- **Keep the OpenF1 JSONL files.** They're a realistically messy dataset for Phase 2 cleaning practice.

Logged in [decisions.md](../decisions.md).

## Files touched

[ROADMAP.md](../../ROADMAP.md) (audit section). No code changed. The bugs are listed as Phase 2 checkboxes, not fixed.

## Next step

Frame the project and write the roadmap → [03](03-framing-and-roadmap.md).

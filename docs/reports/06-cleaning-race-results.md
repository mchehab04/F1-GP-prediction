# 06 — Cleaning race results (`classified_position`)

**Date:** 2026-09-16 → 2026-09-19 · **Phase:** Phase 2 (Data Cleaning)

**In short:** [python/clean_data.py](../../python/clean_data.py) cleans and normalizes `race_results` across all 2,146 rows. It standardizes `classified_position` into four clean categories (`1`–`20`, `'R'`, `'D'`, `'W'`) and resolves the only two `NULL` entries in the dataset (Mick Schumacher in 2022 R2 and Lance Stroll in 2023 R15) by imputing `position = 20` and `grid_position = 20`.

## Why this was needed

In [04](04-first-database-fastf1-duckdb.md), I noted several quirks in the raw FastF1 `race_results`:

1. **Lapped cars were labeled inconsistently:** 2022 used `+1 Lap`, `+2 Laps`, `+6 Laps`, while 2023+ used `Lapped`.
2. **Late retirements were coded as finishers:** Under FIA rules, a driver who completes 90% of the race distance is officially "classified" even if they crashed or retired with engine failure on the penultimate lap. For example, a driver with `status = 'Collision damage'` had `classified_position = '19'`. For predicting race finishes and tracking DNFs, that's misleading.
3. **Disqualifications were coded two ways:** 10 drivers had `status = 'Disqualified'`, but only 7 showed `classified_position = 'D'`. The other 3 showed a finishing position number.
4. **Non-starters vs. withdrawals:** 16 rows had `status = 'Did not start'` and 3 had `status = 'Withdrew'`.
5. **Two rows had `NULL` for both `position` and `grid_position`:** Mick Schumacher (Saudi Arabia 2022) and Lance Stroll (Singapore 2023). Both crashed heavily in qualifying and were withdrawn by their teams before Sunday's race procedures began.

## The cleaning rules

The script performs two idempotent updates:

### 1. Standardizing `classified_position`

```sql
UPDATE race_results
SET classified_position = CASE
    WHEN lower(status) = 'finished' OR lower(status) LIKE '%lap%' THEN CAST(position AS VARCHAR)
    WHEN status IN ('Withdrew', 'Did not start') THEN 'W'
    WHEN status = 'Disqualified' THEN 'D'
    ELSE 'R'
END
```

### 2. Imputing null positions for withdrawn drivers

```sql
UPDATE race_results
SET position = 20, grid_position = 20
WHERE (year = 2022 AND round = 2 AND driver = 'MSC')
   OR (year = 2023 AND round = 15 AND driver = 'STR')
```

**Why position 20 and grid 20?**
- In both events, only 19 cars took the start, occupying grid slots 1 through 19. That left **slot 20 completely vacant**.
- In Schumacher's race, setting his grid position to his qualifying position (14) would have caused a collision with Daniel Ricciardo, who received a 3-place penalty that was shifted up to grid slot 14 when the FIA collapsed the grid after Schumacher's withdrawal.
- Setting both to 20 aligns with every other DNS entry in the database (which have `position = 20`), avoids grid slot collisions, and eliminates all nulls from `race_results`.

### Breakdown of the cleaned data (2,146 rows)

| Category | Statuses Included | Row Count | New `classified_position` |
|---|---|---|---|
| **Classified Finishers** | `Finished`, `Lapped`, `+1 Lap`, `+2 Laps`, `+6 Laps` | 1,829 | `'1'` through `'20'` (matches `position`) |
| **Retirements (DNF)** | `Retired`, `Accident`, `Collision`, `Engine`, `Power Unit`, `Hydraulics`, and other mechanical failures (24 distinct reasons) | 288 | `'R'` |
| **Non-starters (DNS/WD)** | `Did not start` (16), `Withdrew` (3) | 19 | `'W'` |
| **Disqualified (DSQ)** | `Disqualified` | 10 | `'D'` |

## Things that bit me (and how to run it)

- **DuckDB file locking on Windows:** DuckDB allows multiple concurrent readers, but on Windows it cannot open a database file with write access (`read_only=False`) while another process has it open. If `python sql_ui.py` is running, `clean_data.py` will fail with an IO error.
- **The workflow:**
  1. Press `Enter` in the terminal running `python sql_ui.py` to stop the UI.
  2. Run `python python/clean_data.py`.
  3. Restart `python python/sql_ui.py`.
- The script is idempotent: running it again produces the exact same clean results safely.


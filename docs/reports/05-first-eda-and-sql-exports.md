# 05 — First EDA queries and SQL exports

**Date:** 2026-09-16 · **Phase:** Phase 3 (Exploratory Data Analysis)

**In short:** With the database built, I started exploring the data directly in SQL using DuckDB's browser editor ([python/sql_ui.py](../../python/sql_ui.py)). Queries are organized under `sql/eda/`, and query results are exported as CSV files into `data/exports/` using DuckDB's `COPY ... TO` command. I also added a fifth table, `drivers`, to track driver numbers and mid-season team moves.

## What was added to the database

Before digging into teammate matchups, I needed a clean way to handle driver numbers and team changes:

- **`drivers` table:** `(year, driver, team_name, driver_number)` with a composite primary key.
- One row per driver per team per season. This handles mid-season swaps (e.g. Liam Lawson and Yuki Tsunoda swapping between Red Bull and Racing Bulls in 2025) and number changes (Max Verstappen switching between #1 and #3).
- Added to [python/create_db.py](../../python/create_db.py) via `add_driver_info(con)`, reading driver numbers from race sessions.

## The EDA queries

I broke the initial queries into three areas under `sql/eda/`:

### 1. Teammate head-to-head (`sql/eda/teammate_h2h/`)

The teammate is the only driver with the same machinery, so intra-team gaps isolate driver performance from car performance:

- `teammates_per_season.sql`: identifies teammate pairings by finding drivers who shared the same `team_name` in the same race.
- `faster_teammate_practice.sql`: calculates the lap time gap (in seconds) between teammates in FP1, FP2, and FP3.
- `faster_teammate_quali.sql`: calculates the qualifying gap and compares who qualified ahead.
- `faster_teammate_race.sql`: compares race finishing positions and position gaps.
- `points_h2h.sql`: aggregates total points scored by each teammate across the season.

### 2. Race statistics (`sql/eda/race_statistics/`)

Looking at baseline metrics that help frame race predictability:

- `avg_finish_pos.sql`: average finishing position per driver per season.
- `pole_to_win.sql` & `p2w_conv_pct.sql`: how often the pole-sitter wins the race (overall conversion sits around 55–60%).
- `race_completion_pct.sql`: proportion of races completed vs. retirements per driver.

### 3. Most P1s (`sql/eda/most_P1/`)

Season dominance summaries:

- `wins_per_season.sql`: race wins per driver per season.
- `poles_per_season.sql`: pole positions per season.
- `practice_P1_per_season.sql`: who topped the most practice sessions.

## How the export workflow works

DuckDB makes exporting query results painless without needing Python export scripts. Wrapping any query in `COPY (...) TO 'data/exports/...csv'` writes the result straight to disk from the browser UI:

```sql
COPY (
    SELECT ...
) TO 'data/exports/teammate_h2h/teammate_gaps_in_practice.csv';
```

`sql_ui.py` sets the working directory to the project root and ensures `data/exports/` exists so relative export paths always resolve correctly.

## Observations and what to explore next

- **Comparing race finishes needs clean races:** Comparing teammate finishing positions directly without filtering out mechanical DNFs gives an inaccurate picture of driver pace. The next step is looking at "both finished" races.
- **Qualifying gaps vs. race pace:** A driver might be faster over one lap on Saturday but struggle with tire wear on Sunday. Comparing qualifying gaps with race position changes will help spot who has a "Saturday car" vs. a "Sunday car."
- **Data encoding got in the way:** While querying `race_results`, the mixed values in `classified_position` made filtering finishers vs. retirements clunky. That led straight into the first cleaning task in report 06.

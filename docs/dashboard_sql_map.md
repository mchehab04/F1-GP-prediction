# Dashboard SQL map

**Last updated:** 2026-09-23 · **Covers:** `python/dashboard/data_layer.py` and the pages in `python/dashboard/views/`

This page records which of my EDA queries in [`sql/eda/`](../sql/eda/) made it onto the dashboard, what changed along the way, and which dashboard queries are new.

> [!NOTE]
> The dashboard never reads the files in `sql/eda/`. Every chart runs its own query string in [`data_layer.py`](../python/dashboard/data_layer.py). "Same logic" below means an EDA query's logic was carried into one of those functions, usually with a season filter added or several queries merged.

## Foundations

These two cleaning updates change the database itself. Every page depends on them.

| File | What the dashboard relies on |
|---|---|
| [`data_cleaning/cleaning_classified_position.sql`](../sql/eda/data_cleaning/cleaning_classified_position.sql) | `classified_position` values (`1`–`20`, `R`, `D`, `W`) behind every DNF, "classified" and "clean race" filter |
| [`data_cleaning/normalizing_race_locations.sql`](../sql/eda/data_cleaning/normalizing_race_locations.sql) | Consistent circuit names on the Circuits page, the calendar and the Race Explorer |

## 1. My queries used with the same logic

| My file | Dashboard function | Page → visual | What changed |
|---|---|---|---|
| [`most_P1/multiple_grid_wins.sql`](../sql/eda/most_P1/multiple_grid_wins.sql) | `get_wins_by_grid` | Qualifying & Grid → "Where winners started" heatmap | Nothing |
| [`race_statistics/fp3_to_pole_conv.sql`](../sql/eda/race_statistics/fp3_to_pole_conv.sql) | `get_fp3_pole_conversion` | Qualifying & Grid → "FP3 pace → pole" | Nothing |
| [`race_statistics/season_avg_penalties.sql`](../sql/eda/race_statistics/season_avg_penalties.sql) | `get_grid_drops_by_season` | Reliability → "By season" chart and the grid-drop tile | Nothing |
| [`race_statistics/driver_avg_penalties.sql`](../sql/eda/race_statistics/driver_avg_penalties.sql) | `get_grid_drops` | Reliability → "Started behind qualifying slot" | Filtered to one season; adds team |
| [`race_statistics/race_completion_pct.sql`](../sql/eda/race_statistics/race_completion_pct.sql) | `get_reliability` | Reliability → "Finish rate" chart and tiles | Adds team; guards against dividing by zero |
| [`race_statistics/track_overtaking.sql`](../sql/eda/race_statistics/track_overtaking.sql) | `get_overtaking_by_year` | Circuits → "Places changed by season" heatmap | Nothing |
| [`most_P1/wins_per_season.sql`](../sql/eda/most_P1/wins_per_season.sql) | `get_era_leaderboard` (`wins`) | Championship → Era dominance, Wins tab | Merged with the next three into one query |
| [`most_P1/poles_per_season.sql`](../sql/eda/most_P1/poles_per_season.sql) | `get_era_leaderboard` (`poles`) | Era dominance, Poles tab | Merged |
| [`most_P1/practice_P1_per_season.sql`](../sql/eda/most_P1/practice_P1_per_season.sql) | `get_era_leaderboard` (`practice_p1`), `get_practice_toppers` | Era dominance, Practice P1 tab; Practice & Sprints → "Session toppers" | Second copy is one season, split by FP1/FP2/FP3 |
| [`teammate_h2h/clean_h2h.sql`](../sql/eda/teammate_h2h/clean_h2h.sql) | `get_teammate_battles` (`race_d1`, `race_d2`) | Teammates cards → "Race" row | Merged into one teammate query |
| [`teammate_h2h/faster_teammate_quali.sql`](../sql/eda/teammate_h2h/faster_teammate_quali.sql) | `get_teammate_battles` (`quali_d1`, `quali_d2`) | Teammates cards → "Qualifying" row | Totalled per pair instead of listed per round |
| [`teammate_h2h/points_h2h.sql`](../sql/eda/teammate_h2h/points_h2h.sql) | `get_teammate_battles` (`points_d1`, `points_d2`) | Teammates cards → "Points" row | Merged |
| [`teammate_h2h/q3_app_pct.sql`](../sql/eda/teammate_h2h/q3_app_pct.sql) | `get_teammate_battles` (`q3_pct_d1`, `q3_pct_d2`) | Teammates cards → "Q3 rate" row | Merged |
| [`teammate_h2h/median_quali_gap.sql`](../sql/eda/teammate_h2h/median_quali_gap.sql) | `get_teammate_battles` (`median_gap_s`) | Teammates cards → "X faster by …s" footer | Same same-session comparison (Q3 vs Q3, else Q2, else Q1) |

## 2. My queries used with real changes

| My file | Dashboard function | Page → visual | What changed |
|---|---|---|---|
| [`race_statistics/p2w_conv_pct.sql`](../sql/eda/race_statistics/p2w_conv_pct.sql) | `get_pole_conversion` | Qualifying & Grid → "Poles converted to wins" and the "Pole → win" tile | All seasons combined instead of per year |
| [`most_P1/front_row_conversion.sql`](../sql/eda/most_P1/front_row_conversion.sql) | `get_pole_conversion` (`front_row_wins`) | Qualifying & Grid → "Wins from front row" tile | Folded into the pole query; totalled across drivers |
| [`race_statistics/pole_to_win.sql`](../sql/eda/race_statistics/pole_to_win.sql) | Python in `views/race_hub.py`, using `get_season_calendar` | Race Hub → "Won from pole" figure | Same idea: counts races where the pole-sitter won |
| [`most_P1/sprint_race_winners.sql`](../sql/eda/most_P1/sprint_race_winners.sql) | `get_sprint_summary` | Practice & Sprints → "Sprint points" | Adds podiums, points and team; keeps point scorers, not only winners |
| [`most_P1/total_driver_wins.sql`](../sql/eda/most_P1/total_driver_wins.sql) | `get_era_leaderboard` | Number beside each driver in the Era dominance heatmap (e.g. VER 51) | Sum of the per-season rows; drops the unneeded self-join |
| [`most_P1/total_constructor_wins.sql`](../sql/eda/most_P1/total_constructor_wins.sql) | `get_constructor_standings` (`wins`) | Championship → constructors hover; Race Hub → constructor leader card | Per season instead of all seasons |

## 3. My queries not on the dashboard

| My file | Status |
|---|---|
| [`teammate_h2h/concordance_pct.sql`](../sql/eda/teammate_h2h/concordance_pct.sql) | Not used |
| [`teammate_h2h/faster_teammate_practice.sql`](../sql/eda/teammate_h2h/faster_teammate_practice.sql) | Not used |
| [`teammate_h2h/faster_teammate_race.sql`](../sql/eda/teammate_h2h/faster_teammate_race.sql) | Not used; race head-to-head uses the clean-race logic from `clean_h2h.sql` |
| [`teammate_h2h/teammates_per_season.sql`](../sql/eda/teammate_h2h/teammates_per_season.sql) | Not used; teammate pairs are built race by race, which handles mid-season swaps (e.g. LAW/TSU in 2025) |
| [`teammate_h2h/avg_pos_gained.sql`](../sql/eda/teammate_h2h/avg_pos_gained.sql) | Calculated in `get_teammate_battles` (`gained_d1`, `gained_d2`) but not shown on the cards |
| [`most_P1/num_of_grid_spots_won_from.sql`](../sql/eda/most_P1/num_of_grid_spots_won_from.sql) | Only indirectly, as the "Winning slots" tile on Qualifying & Grid |
| [`data_cleaning/null_values.sql`](../sql/eda/data_cleaning/null_values.sql) | Not used |
| [`data_cleaning/distinct_status.sql`](../sql/eda/data_cleaning/distinct_status.sql) | Not used; its status values informed the retirement-cause grouping |

## 4. Queries already in the dashboard before the redesign

These 10 functions were in `data_layer.py` before the redesign. Only `get_circuit_dna` was changed, so that a track appearing under two Grand Prix names (Barcelona in 2026) is counted once.

| Function | Closest EDA file | Page → visual |
|---|---|---|
| `get_circuit_dna` | `track_avg_dnfs.sql` + `track_overtaking.sql` + pole → win | Circuits → "Chaos vs. overtaking" scatter and circuit guide tiles; Race Predictor inputs |
| `get_teammate_quali_gaps` | `median_quali_gap.sql`, but compares each driver's best lap from any session | Teammates → "Median gap" chart |
| `get_weekend_evolution` | `weekend_evolution.sql` | Practice & Sprints → "Track evolution" (FP1 → qualifying difference worked out in Python) |
| `get_driver_form` | `avg_finish_pos.sql` | Race Predictor → season average finish and default driver (points leader) |
| `get_grid_win_conversion` | none | Qualifying & Grid → "What each grid slot is worth" |
| `get_seasons` | none | Sidebar season picker |
| `get_drivers_for_year` | none | Race Predictor → driver list |
| `get_kpis` | none | **Unused** since the redesign |
| `get_season_races` | none | **Unused** |
| `get_teammate_clean_h2h` | `clean_h2h.sql` | **Unused**; replaced by `get_teammate_battles` |

## 5. New queries

| Function | What it returns | Page → visual |
|---|---|---|
| `get_season_calendar` | Every round with winner, winner's grid slot and pole-sitter | Race Hub → header and calendar; Race Explorer → race picker |
| `get_driver_standings` | Points (race + sprint), wins, podiums, poles, DNFs, average finish | Championship → drivers table; Race Hub → leader card |
| `get_constructor_standings` | Team points (race + sprint), wins, podiums, DNFs | Championship → constructors bars; Race Hub → constructor card |
| `get_points_progression` | Running points total per round, by driver or team | Race Hub → "Championship battle"; Championship → constructors trajectory |
| `get_race_results` | One race's classification | Race Explorer → grid-to-finish chart and classification; Race Hub → podium |
| `get_quali_results` | One qualifying session with Q1–Q3 times | Race Explorer → "Gap to pole" |
| `get_circuit_history` | Winner, grid slot, pole and DNFs at one track per year | Circuits → track history |
| `get_retirement_causes` | Retirements grouped as incident, technical or unspecified | Reliability → "Retirements by team" |
| `get_data_coverage` | Row counts per table per season | Methodology → coverage heatmap |

Shared helper: `SEASON_POINTS_CTE` adds race and sprint points together for the standings and progression queries.

## Known gaps

| Issue | Where | Effect |
|---|---|---|
| Pit-lane starts counted as grid slot 0 | `get_circuit_dna` (overtaking index) | Inflates that circuit's overtaking figure; `track_overtaking.sql` correctly uses P20 |
| Different DNF definitions | `get_circuit_dna` counts `R`, `D`, `W`; `track_avg_dnfs.sql` and `get_circuit_history` count only `R` | Circuit scatter and track history can disagree |
| Calculated but not shown | `avg_finish` in `get_driver_standings`; `gained_d1`/`gained_d2` in `get_teammate_battles` | No visible effect |
| Dead code | `get_kpis`, `get_season_races`, `get_teammate_clean_h2h`, `make_tug_of_war_chart` | Safe to delete |

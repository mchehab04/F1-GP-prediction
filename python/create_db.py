# create a database to store the Grand Prix info for the 2022-2026 seasons

import pandas as pd
import fastf1
import duckdb
from pathlib import Path

YEARS = [2022, 2023, 2024, 2025, 2026]
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "f1_db.duckdb"
DB_PATH.parent.mkdir(exist_ok=True)                # duckdb creates the file, not the folder
fastf1.Cache.enable_cache(ROOT / "fastf1_cache")   # reuse the cache already on disk

# Function that adds the races to the database
def add_races(con):
    # Seasons already saved - skipped so a rerun doesn't hit the primary key
    done = {r[0] for r in con.execute("SELECT DISTINCT year FROM races").fetchall()}
    for year in YEARS:
        if year in done:
            continue
        print(f"Loading races for year {year}")
        sched = fastf1.get_event_schedule(year, include_testing=False)
        # DuckDB can query the pandas DataFrame `sched` directly by its variable name
        con.execute("""
            INSERT INTO races
            SELECT ?, RoundNumber, EventName, Location, Country, EventFormat LIKE 'sprint%'
            FROM sched
        """, [year])  

def add_quali_results(con):
    # Loop over (year, round) pairs - round numbers are unique within a year, names are not
    races = con.execute("SELECT year, round FROM races ORDER BY year, round").fetchall()
    # Sessions already saved - skipped so a rerun only fetches what is missing
    done = set(con.execute("SELECT DISTINCT year, round FROM quali_results").fetchall())
    for year, rnd in races:
        if (year, rnd) in done:
            continue
        session = fastf1.get_session(year, rnd, "Q")      # "Q" = qualifying
        if session.date > pd.Timestamp.now():             # skip races that haven't happened yet
            continue
        print(f"Loading qualifying {year} round {rnd}")
        session.load(laps=False, telemetry=False, weather=False, messages=False)  # results only
        res = session.results                             # a DataFrame, one row per driver
        if res["Position"].isna().all():                  # FastF1 only warns when the fetch fails
            print(f"  WARNING: no results for {year} round {rnd}, skipping - rerun later")
            continue
        df = pd.DataFrame({
            "year": year,
            "round": rnd,
            "driver": res["Abbreviation"],
            "position": res["Position"],
            "q1": res["Q1"].dt.total_seconds(),           # Timedelta -> seconds, e.g. 90.031
            "q2": res["Q2"].dt.total_seconds(),
            "q3": res["Q3"].dt.total_seconds(),
        })
        con.execute("INSERT INTO quali_results SELECT * FROM df")

def add_race_results(con):
    # Loop over (year, round) pairs - round numbers are unique within a year, names are not
    races = con.execute("SELECT year, round FROM races ORDER BY year, round").fetchall()
    # Races already saved - skipped so a rerun only fetches what is missing
    done = set(con.execute("SELECT DISTINCT year, round FROM race_results").fetchall())
    for year, rnd in races:
        if (year, rnd) in done:
            continue
        session = fastf1.get_session(year, rnd, "R")      # "R" = race
        if session.date > pd.Timestamp.now():             # skip races that haven't happened yet
            continue
        print(f"Loading race results for {year} round {rnd}")
        session.load(laps=False, telemetry=False, weather=False, messages=False)  # results only
        res = session.results                             # a DataFrame, one row per driver
        if res["Position"].isna().all():                  # FastF1 only warns when the fetch fails
            print(f"  WARNING: no results for {year} round {rnd}, skipping - rerun later")
            continue
        df = pd.DataFrame({
            "year": year,
            "round": rnd,
            "driver": res["Abbreviation"],
            "position": res["Position"],
            "grid_position": res["GridPosition"],        # where they actually started
            "team_name": res["TeamName"],
            "status": res["Status"],                     # "Finished", "+1 Lap", "Accident", ...
            "classified_position": res["ClassifiedPosition"],   # "R" = retired, "D" = disqualified
            "points": res["Points"],
            "laps": res["Laps"],                         # laps completed
        })
        # Name the columns so the insert doesn't depend on column order
        con.execute("""INSERT INTO race_results
            (year, round, driver, position, grid_position, team_name, status,
             classified_position, points, laps)
            SELECT year, round, driver, position, grid_position, team_name, status,
                   classified_position, points, laps FROM df""")

def get_practice_session_results(con):
    # Loop over (year, round) pairs - round numbers are unique within a year, names are not
    races = con.execute("SELECT year, round FROM races ORDER BY year, round").fetchall()
    # Sessions already saved - skipped so a rerun (e.g. after a rate limit) resumes where it stopped
    done = set(con.execute("SELECT DISTINCT year, round, session FROM practice_results").fetchall())
    for year, rnd in races:
        for session_type in ["FP1", "FP2", "FP3"]:
            if (year, rnd, session_type) in done:
                continue
            try:
                session = fastf1.get_session(year, rnd, session_type)
            except ValueError:                                # session not in this weekend's format
                continue                                      # (sprint weekends 2023+ have no FP2/FP3; 2022 had FP2)
            if session.date > pd.Timestamp.now():             # skip races that haven't happened yet
                continue
            print(f"Loading practice results for {year} round {rnd} - {session_type}")
            # Practice has no official results feed (Position is always empty), so rank from lap times
            session.load(laps=True, telemetry=False, weather=False, messages=False)
            try:
                laps = session.laps
            except fastf1.exceptions.DataNotLoadedError:     # download failed - FastF1 only logs warnings
                print(f"  WARNING: no lap data for {year} round {rnd} {session_type}, skipping - rerun later")
                continue
            # IsPersonalBest excludes deleted laps (track limits), matching the official classification
            best = (laps[laps["IsPersonalBest"] == True]
                    .groupby("Driver")["LapTime"].min()
                    .dt.total_seconds()
                    .sort_values())
            if best.empty:
                print(f"  WARNING: no valid laps for {year} round {rnd} {session_type}, skipping")
                continue
            df = pd.DataFrame({
                "year": year,
                "round": rnd,
                "session": session_type,                      # FP1, FP2, FP3
                "driver": best.index,
                "position": range(1, len(best) + 1),
                "best_lap": best.values,                      # seconds, e.g. 92.869
            })
            con.execute("INSERT INTO practice_results SELECT * FROM df")

def add_driver_info(con):
    # One row per driver per team per season: a driver can change team mid-season
    # (LAW/TSU swapped Red Bull and Racing Bulls in 2025) and numbers can change
    # between seasons (VER: 1 in 2025, 3 in 2026).
    # race_results already knows who drove for which team - find the combinations not saved yet
    missing = con.execute("""
        SELECT rr.year, rr.driver, rr.team_name, min(rr.round) AS first_round
        FROM race_results rr
        ANTI JOIN drivers d
            ON d.year = rr.year AND d.driver = rr.driver AND d.team_name = rr.team_name
        GROUP BY rr.year, rr.driver, rr.team_name
        ORDER BY rr.year, first_round
    """).fetchall()
    results = {} # (year, round) -> results, so each race loads once
    for year, driver, team_name, first_round in missing:
        if (year, first_round) not in results:
            print(f"Loading driver info from {year} round {first_round}")
            session = fastf1.get_session(year, first_round, "R")
            session.load(laps=False, telemetry=False, weather=False, messages=False)  # results only
            results[(year, first_round)] = session.results.set_index("Abbreviation")
        row = results[(year, first_round)].loc[driver]    # this driver's line in that race's results
        con.execute("""
            INSERT INTO drivers (year, driver, team_name, driver_number)
            VALUES (?, ?, ?, ?)
        """, [year, driver, team_name, int(row["DriverNumber"])])

def add_sprint_results(con):
    # Only loop over events that actually hosted a sprint race
    races = con.execute("SELECT year, round FROM races WHERE sprint_included = true ORDER BY year, round").fetchall()
    done = set(con.execute("SELECT DISTINCT year, round FROM sprint_results").fetchall())
    for year, rnd in races:
        if (year, rnd) in done:
            continue
        try:
            session = fastf1.get_session(year, rnd, "Sprint")
        except ValueError:
            continue  # Safety check in case of schedule changes
        if session.date > pd.Timestamp.now():             # skip races that haven't happened yet
            continue
        print(f"Loading sprint results for {year} round {rnd}")
        session.load(laps=False, telemetry=False, weather=False, messages=False)  # results only
        res = session.results                             # a DataFrame, one row per driver
        if res["Position"].isna().all():                  # FastF1 only warns when the fetch fails
            print(f"  WARNING: no results for {year} round {rnd}, skipping - rerun later")
            continue
        df = pd.DataFrame({
            "year": year,
            "round": rnd,
            "driver": res["Abbreviation"],
            "position": res["Position"],
            "grid_position": res["GridPosition"],        # where they actually started
            "team_name": res["TeamName"],
            "status": res["Status"],                     # "Finished", "+1 Lap", "Accident", ...
            "classified_position": res["ClassifiedPosition"],   # "R" = retired, "D" = disqualified
            "points": res["Points"],
            "laps": res["Laps"],                         # laps completed
        })
        # Name the columns so the insert doesn't depend on column order
        con.execute("""INSERT INTO sprint_results
            (year, round, driver, position, grid_position, team_name, status,
             classified_position, points, laps)
            SELECT year, round, driver, position, grid_position, team_name, status,
                   classified_position, points, laps FROM df""")

def main():
    with duckdb.connect(str(DB_PATH)) as con:
        # create the races table
        con.execute("""
            CREATE TABLE IF NOT EXISTS races (
                year            INTEGER,
                round           INTEGER,
                event_name      VARCHAR,
                location        VARCHAR,
                country         VARCHAR,
                sprint_included BOOLEAN,
                PRIMARY KEY (year, round)
            )
        """)
        add_races(con)

        # create the quali_results table
        con.execute("""
            CREATE TABLE IF NOT EXISTS quali_results (
                year            INTEGER,
                round           INTEGER,
                driver          VARCHAR,
                position        INTEGER,
                q1              DOUBLE,
                q2              DOUBLE,
                q3              DOUBLE,
                PRIMARY KEY (year, round, driver)
            )
        """)
        add_quali_results(con)

        # create the race_results table (IF NOT EXISTS keeps rows from earlier runs)
        con.execute("""
            CREATE TABLE IF NOT EXISTS race_results (
                year                INTEGER, -- Year of the race
                round               INTEGER, -- Round number
                driver              VARCHAR, -- Driver abbreviation
                position            INTEGER, -- Finishing position
                grid_position       INTEGER, -- Grid position
                team_name           VARCHAR, -- Team name
                status              VARCHAR, -- Race status (Finished, +1 Lap, etc.)
                classified_position VARCHAR, -- Classified position (R = retired, D = disqualified)
                points              INTEGER, -- Points scored
                laps                INTEGER, -- Laps completed
                PRIMARY KEY (year, round, driver)
            )
        """)
        add_race_results(con)

        # create the practice_results table (IF NOT EXISTS keeps rows from earlier runs)
        con.execute("""
            CREATE TABLE IF NOT EXISTS practice_results (
                year            INTEGER,
                round           INTEGER,
                session         VARCHAR,
                driver          VARCHAR,
                position        INTEGER,
                best_lap        DOUBLE,
                PRIMARY KEY (year, round, session, driver)
            )
        """)
        get_practice_session_results(con)

        # create the drivers table - one row per driver per team per season
        con.execute("""
            CREATE TABLE IF NOT EXISTS drivers (
                year            INTEGER,
                driver          VARCHAR,  -- abbreviation, e.g. VER (same name as in the results tables)
                team_name       VARCHAR,  -- a driver who changed team mid-season has one row per team
                driver_number   INTEGER,  -- can change between seasons (VER: 1 in 2025, 3 in 2026)
                PRIMARY KEY (year, driver, team_name)
            )
        """)
        add_driver_info(con)

        # create sprint_results table
        con.execute("""
            CREATE TABLE IF NOT EXISTS sprint_results (
                year            INTEGER,
                round           INTEGER,
                driver          VARCHAR,
                position        INTEGER,
                grid_position   INTEGER,
                team_name       VARCHAR,
                status          VARCHAR,
                classified_position VARCHAR,
                points          INTEGER,
                laps            INTEGER,
                PRIMARY KEY (year, round, driver)
            )
        """)
        add_sprint_results(con)

if __name__ == '__main__':
    main()
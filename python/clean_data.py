"""
Clean and normalize race_results in DuckDB:
- If status is 'Finished' or contains 'lap' (case-insensitive), set classified_position = position
- If status is 'Withdrew' or 'Did not start', set classified_position = 'W'
- If status is 'Disqualified', set classified_position = 'D'
- Any other status is set to 'R' (all other statuses indicate a DNF)
- Impute null position and grid_position for withdrawn drivers (MSC 2022 R2, STR 2023 R15) to 20
"""

import sys
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "f1_db.duckdb"


def show_distinct_statuses(con):
    print("\n--- Distinct Statuses in race_results ---")
    rows = con.execute(
        "SELECT DISTINCT status, count(*) AS count FROM race_results GROUP BY status ORDER BY count DESC"
    ).fetchall()
    for status, count in rows:
        print(f"  {status:<20} : {count} rows")


def clean_race_results(con):
    print("\nApplying cleaning logic to race_results.classified_position...")
    con.execute("""
        UPDATE race_results
        SET classified_position = CASE
            WHEN lower(status) = 'finished' OR lower(status) LIKE '%lap%' THEN CAST(position AS VARCHAR)
            WHEN status IN ('Withdrew', 'Did not start') THEN 'W'
            WHEN status = 'Disqualified' THEN 'D'
            ELSE 'R'
        END
    """)
    print("Classified positions updated successfully!")


def clean_null_positions(con):
    print("\nImputing null grid_position and position for withdrawn drivers...")
    # In both 2022 R2 (MSC) and 2023 R15 (STR), 19 cars occupied grid slots 1-19,
    # leaving slot 20 empty. Setting both to 20 resolves nulls and avoids grid collisions.
    con.execute("""
        UPDATE race_results
        SET position = 20, grid_position = 20
        WHERE (year = 2022 AND round = 2 AND driver = 'MSC')
           OR (year = 2023 AND round = 15 AND driver = 'STR')
    """)
    print("Null positions updated successfully!")


def show_cleaning_summary(con):
    print("\n--- Summary of cleaned classified_position by status ---")
    summary = con.execute("""
        SELECT
            classified_position,
            status,
            count(*) AS count
        FROM race_results
        GROUP BY classified_position, status
        ORDER BY classified_position, count DESC
    """).fetchall()

    for pos, status, count in summary:
        print(f"  classified_position={pos:<4} | status={status:<20} | {count} rows")

    print("\n--- Verification of previously NULL positions (MSC 2022 R2, STR 2023 R15) ---")
    null_rows = con.execute("""
        SELECT year, round, driver, position, grid_position, status, classified_position
        FROM race_results
        WHERE (year = 2022 AND round = 2 AND driver = 'MSC')
           OR (year = 2023 AND round = 15 AND driver = 'STR')
    """).fetchall()
    for r in null_rows:
        print(f"  {r[0]} R{r[1]:<2} {r[2]}: position={r[3]}, grid_position={r[4]}, status={r[5]}, classified={r[6]}")


def main():
    try:
        con = duckdb.connect(str(DB_PATH), read_only=False)
    except duckdb.IOException as e:
        print("\n[ERROR] Unable to open DuckDB with write access.")
        print("On Windows, DuckDB locks the file if another process has it open.")
        print("Please stop 'python sql_ui.py' (press Enter in its terminal) and run this script again.\n")
        sys.exit(1)

    try:
        show_distinct_statuses(con)
        clean_race_results(con)
        clean_null_positions(con)
        show_cleaning_summary(con)
    finally:
        con.close()


if __name__ == "__main__":
    main()

import duckdb
import pandas as pd
import streamlit as st
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "f1_db.duckdb"))

TEAM_COLORS = {
    "Red Bull": "#3671C6",
    "Ferrari": "#E8002D",
    "McLaren": "#FF8000",
    "Mercedes": "#00D2BE",
    "Aston Martin": "#229971",
    "Alpine": "#0093CC",
    "Williams": "#64C4FF",
    "Racing Bulls": "#6692FF",
    "RB": "#6692FF",
    "Audi": "#9B1B30",
    "Cadillac": "#C7A76C",
    "AlphaTauri": "#5E8FAA",
    "Sauber": "#52E252",
    "Alfa Romeo": "#C92D4B",
    "Haas": "#B6BABD",
}

def get_team_color(team_name: str) -> str:
    if not team_name:
        return "#A1A1AA"
    for k, v in TEAM_COLORS.items():
        if k.lower() in team_name.lower():
            return v
    return "#E10600"

def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)

@st.cache_data(ttl=3600)
def get_kpis():
    con = get_connection()
    stats = con.execute("""
        SELECT 
            (SELECT count(*) FROM races) as total_races,
            (SELECT count(distinct driver) FROM drivers) as total_drivers,
            (SELECT count(*) FROM race_results) as total_entries,
            (SELECT min(year) || '–' || max(year) FROM races) as era_years
    """).df().to_dict(orient="records")[0]
    con.close()
    return stats

@st.cache_data(ttl=3600)
def get_seasons():
    con = get_connection()
    df = con.execute("SELECT DISTINCT year FROM races ORDER BY year DESC").df()
    con.close()
    return df["year"].tolist()

@st.cache_data(ttl=3600)
def get_season_races(year: int):
    con = get_connection()
    df = con.execute("""
        SELECT round, event_name, location, country, sprint_included
        FROM races
        WHERE year = ?
        ORDER BY round ASC
    """, [year]).df()
    con.close()
    return df

@st.cache_data(ttl=3600)
def get_drivers_for_year(year: int):
    con = get_connection()
    df = con.execute("""
        SELECT DISTINCT d.driver, d.team_name, d.driver_number
        FROM drivers d
        WHERE d.year = ?
        ORDER BY d.team_name, d.driver
    """, [year]).df()
    con.close()
    return df

@st.cache_data(ttl=3600)
def get_teammate_clean_h2h(year: int):
    con = get_connection()
    query = """
        WITH pair_results AS (
            SELECT 
                r1.year,
                r1.round,
                r1.team_name,
                r1.driver AS d1,
                r2.driver AS d2,
                r1.position AS p1,
                r2.position AS p2
            FROM race_results r1
            JOIN race_results r2 
              ON r1.year = r2.year 
             AND r1.round = r2.round 
             AND r1.team_name = r2.team_name
             AND r1.driver < r2.driver
            WHERE r1.classified_position NOT IN ('R', 'D', 'W')
              AND r2.classified_position NOT IN ('R', 'D', 'W')
              AND r1.year = ?
        )
        SELECT 
            team_name,
            d1,
            d2,
            COUNT(CASE WHEN p1 < p2 THEN 1 END) AS d1_wins,
            COUNT(CASE WHEN p2 < p1 THEN 1 END) AS d2_wins,
            COUNT(*) AS total_clean_races
        FROM pair_results
        GROUP BY ALL
        HAVING COUNT(*) > 0
        ORDER BY team_name
    """
    df = con.execute(query, [year]).df()
    con.close()
    return df, query

@st.cache_data(ttl=3600)
def get_teammate_quali_gaps(year: int):
    con = get_connection()
    query = """
        WITH quali_clean AS (
            SELECT 
                q.year,
                q.round,
                d.team_name,
                q.driver,
                LEAST(COALESCE(q.q3, 999), COALESCE(q.q2, 999), COALESCE(q.q1, 999)) AS best_q
            FROM quali_results q
            JOIN drivers d ON q.year = d.year AND q.driver = d.driver
            WHERE q.year = ?
        ),
        pairs AS (
            SELECT 
                q1.year,
                q1.round,
                q1.team_name,
                q1.driver AS d1,
                q2.driver AS d2,
                (q2.best_q - q1.best_q) AS gap_s
            FROM quali_clean q1
            JOIN quali_clean q2 
              ON q1.year = q2.year 
             AND q1.round = q2.round 
             AND q1.team_name = q2.team_name
             AND q1.driver < q2.driver
            WHERE q1.best_q < 999 AND q2.best_q < 999
        )
        SELECT 
            team_name,
            d1,
            d2,
            ROUND(MEDIAN(gap_s), 3) AS median_gap_s,
            COUNT(*) AS sessions_counted
        FROM pairs
        GROUP BY ALL
        HAVING COUNT(*) > 1
        ORDER BY ABS(ROUND(MEDIAN(gap_s), 3)) DESC
    """
    df = con.execute(query, [year]).df()
    con.close()
    return df, query

@st.cache_data(ttl=3600)
def get_circuit_dna():
    con = get_connection()
    query = """
        WITH track_dnf AS (
            SELECT 
                r.location,
                ARG_MAX(r.event_name, r.year) AS event_name,
                ROUND(AVG(dnf_count), 2) AS avg_dnfs
            FROM (
                SELECT 
                    year, 
                    round, 
                    COUNT(CASE WHEN classified_position IN ('R', 'D', 'W') THEN 1 END) AS dnf_count
                FROM race_results
                GROUP BY ALL
            ) d
            JOIN races r ON d.year = r.year AND d.round = r.round
            GROUP BY ALL
        ),
        track_moves AS (
            SELECT 
                r.location,
                ROUND(AVG(ABS(res.position - res.grid_position)), 2) AS overtaking_index
            FROM race_results res
            JOIN races r ON res.year = r.year AND res.round = r.round
            WHERE res.classified_position NOT IN ('R', 'D', 'W')
            GROUP BY ALL
        ),
        pole_conv AS (
            SELECT 
                r.location,
                ROUND(AVG(CASE WHEN res.grid_position = 1 AND res.position = 1 THEN 1.0 ELSE 0.0 END) * 100, 1) AS pole_to_win_pct
            FROM race_results res
            JOIN races r ON res.year = r.year AND res.round = r.round
            WHERE res.grid_position = 1
            GROUP BY ALL
        )
        SELECT 
            d.location,
            d.event_name,
            d.avg_dnfs,
            m.overtaking_index,
            COALESCE(p.pole_to_win_pct, 0.0) AS pole_to_win_pct
        FROM track_dnf d
        JOIN track_moves m ON d.location = m.location
        LEFT JOIN pole_conv p ON d.location = p.location
        ORDER BY d.avg_dnfs DESC
    """
    df = con.execute(query).df()
    con.close()
    return df, query

@st.cache_data(ttl=3600)
def get_weekend_evolution(year: int):
    con = get_connection()
    query = """
        SELECT 
            r.round,
            r.location,
            ROUND(AVG(CASE WHEN p.session = 'FP1' THEN p.best_lap END), 3) AS fp1_avg_s,
            ROUND(AVG(CASE WHEN p.session = 'FP2' THEN p.best_lap END), 3) AS fp2_avg_s,
            ROUND(AVG(CASE WHEN p.session = 'FP3' THEN p.best_lap END), 3) AS fp3_avg_s,
            ROUND(AVG(COALESCE(q.q3, q.q2, q.q1)), 3) AS quali_avg_s
        FROM practice_results p
        JOIN races r ON p.year = r.year AND p.round = r.round
        LEFT JOIN quali_results q ON p.year = q.year AND p.round = q.round AND p.driver = q.driver
        WHERE p.year = ? AND p.best_lap IS NOT NULL AND p.best_lap > 0
        GROUP BY ALL
        ORDER BY r.round
    """
    df = con.execute(query, [year]).df()
    con.close()
    return df, query

@st.cache_data(ttl=3600)
def get_grid_win_conversion():
    con = get_connection()
    query = """
        SELECT 
            grid_position,
            COUNT(*) AS total_starts,
            COUNT(CASE WHEN position = 1 THEN 1 END) AS wins,
            COUNT(CASE WHEN position <= 3 THEN 1 END) AS podiums,
            COUNT(CASE WHEN position <= 10 THEN 1 END) AS points_finishes,
            ROUND(COUNT(CASE WHEN position = 1 THEN 1 END) * 100.0 / COUNT(*), 1) AS win_rate_pct,
            ROUND(COUNT(CASE WHEN position <= 3 THEN 1 END) * 100.0 / COUNT(*), 1) AS podium_rate_pct,
            ROUND(COUNT(CASE WHEN position <= 10 THEN 1 END) * 100.0 / COUNT(*), 1) AS points_rate_pct
        FROM race_results
        WHERE grid_position BETWEEN 1 AND 20
        GROUP BY grid_position
        ORDER BY grid_position ASC
    """
    df = con.execute(query).df()
    con.close()
    return df, query

@st.cache_data(ttl=3600)
def get_driver_form(year: int):
    con = get_connection()
    query = """
        SELECT 
            r.driver,
            r.team_name,
            COUNT(*) AS total_races,
            ROUND(AVG(r.position), 2) AS avg_finish,
            ROUND(AVG(r.grid_position), 2) AS avg_grid,
            COUNT(CASE WHEN r.position = 1 THEN 1 END) AS wins,
            COUNT(CASE WHEN r.position <= 3 THEN 1 END) AS podiums,
            SUM(r.points) AS total_points
        FROM race_results r
        WHERE r.year = ?
        GROUP BY ALL
        ORDER BY total_points DESC
    """
    df = con.execute(query, [year]).df()
    con.close()
    return df


def _run(query: str, params: dict | None = None) -> pd.DataFrame:
    con = get_connection()
    try:
        return con.execute(query, params or {}).df()
    finally:
        con.close()


SEASON_POINTS_CTE = """
    pts AS (
        SELECT round, driver, team_name, points FROM race_results WHERE year = $year
        UNION ALL
        SELECT round, driver, team_name, points FROM sprint_results WHERE year = $year
    )
"""


@st.cache_data(ttl=3600)
def get_season_calendar(year: int):
    query = """
        SELECT
            r.round,
            r.event_name,
            r.location,
            r.country,
            r.sprint_included,
            w.driver AS winner,
            w.team_name AS winner_team,
            w.grid_position AS winner_grid,
            q.driver AS pole
        FROM races r
        LEFT JOIN race_results w ON w.year = r.year AND w.round = r.round AND w.position = 1
        LEFT JOIN quali_results q ON q.year = r.year AND q.round = r.round AND q.position = 1
        WHERE r.year = $year
        ORDER BY r.round
    """
    return _run(query, {"year": year}), query


@st.cache_data(ttl=3600)
def get_driver_standings(year: int):
    query = f"""
        WITH {SEASON_POINTS_CTE},
        totals AS (
            SELECT driver, SUM(points) AS points FROM pts GROUP BY driver
        ),
        race AS (
            SELECT
                driver,
                ARG_MAX(team_name, round) AS team_name,
                COUNT(*) AS starts,
                COUNT(*) FILTER (WHERE position = 1) AS wins,
                COUNT(*) FILTER (WHERE position <= 3) AS podiums,
                COUNT(*) FILTER (WHERE classified_position = 'R') AS dnfs,
                ROUND(AVG(position) FILTER (WHERE classified_position NOT IN ('R', 'D', 'W')), 1) AS avg_finish
            FROM race_results
            WHERE year = $year
            GROUP BY driver
        ),
        poles AS (
            SELECT driver, COUNT(*) AS poles
            FROM quali_results
            WHERE year = $year AND position = 1
            GROUP BY driver
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY t.points DESC, r.wins DESC, r.podiums DESC) AS pos,
            r.driver,
            r.team_name,
            t.points,
            r.wins,
            r.podiums,
            COALESCE(p.poles, 0) AS poles,
            r.dnfs,
            r.avg_finish,
            r.starts
        FROM race r
        JOIN totals t USING (driver)
        LEFT JOIN poles p USING (driver)
        ORDER BY pos
    """
    return _run(query, {"year": year}), query


@st.cache_data(ttl=3600)
def get_constructor_standings(year: int):
    query = f"""
        WITH {SEASON_POINTS_CTE},
        totals AS (
            SELECT team_name, SUM(points) AS points FROM pts GROUP BY team_name
        ),
        race AS (
            SELECT
                team_name,
                COUNT(*) FILTER (WHERE position = 1) AS wins,
                COUNT(*) FILTER (WHERE position <= 3) AS podiums,
                COUNT(*) FILTER (WHERE classified_position = 'R') AS dnfs
            FROM race_results
            WHERE year = $year
            GROUP BY team_name
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY t.points DESC, r.wins DESC) AS pos,
            t.team_name,
            t.points,
            r.wins,
            r.podiums,
            r.dnfs
        FROM totals t
        JOIN race r USING (team_name)
        ORDER BY pos
    """
    return _run(query, {"year": year}), query


@st.cache_data(ttl=3600)
def get_points_progression(year: int, by: str = "driver"):
    key = "team_name" if by == "team" else "driver"
    query = f"""
        WITH {SEASON_POINTS_CTE},
        rounds AS (
            SELECT DISTINCT round FROM race_results WHERE year = $year
        ),
        entities AS (
            SELECT DISTINCT {key} AS name FROM pts
        ),
        per_round AS (
            SELECT round, {key} AS name, SUM(points) AS points FROM pts GROUP BY ALL
        )
        SELECT
            r.round,
            e.name,
            SUM(COALESCE(p.points, 0)) OVER (PARTITION BY e.name ORDER BY r.round) AS cum_points
        FROM rounds r
        CROSS JOIN entities e
        LEFT JOIN per_round p ON p.round = r.round AND p.name = e.name
        ORDER BY r.round, e.name
    """
    return _run(query, {"year": year}), query


@st.cache_data(ttl=3600)
def get_race_results(year: int, round_no: int):
    query = """
        SELECT
            position,
            driver,
            team_name,
            grid_position,
            classified_position,
            status,
            points,
            laps
        FROM race_results
        WHERE year = $year AND round = $round
        ORDER BY position
    """
    return _run(query, {"year": year, "round": round_no}), query


@st.cache_data(ttl=3600)
def get_quali_results(year: int, round_no: int):
    query = """
        SELECT
            q.position,
            q.driver,
            r.team_name,
            q.q1,
            q.q2,
            q.q3,
            LEAST(COALESCE(q.q3, 999), COALESCE(q.q2, 999), COALESCE(q.q1, 999)) AS best
        FROM quali_results q
        LEFT JOIN race_results r ON r.year = q.year AND r.round = q.round AND r.driver = q.driver
        WHERE q.year = $year AND q.round = $round
        ORDER BY q.position
    """
    return _run(query, {"year": year, "round": round_no}), query


@st.cache_data(ttl=3600)
def get_era_leaderboard():
    query = """
        WITH race AS (
            SELECT
                year,
                driver,
                COUNT(*) FILTER (WHERE position = 1) AS wins,
                COUNT(*) FILTER (WHERE position <= 3) AS podiums
            FROM race_results
            GROUP BY ALL
        ),
        quali AS (
            SELECT year, driver, COUNT(*) FILTER (WHERE position = 1) AS poles
            FROM quali_results
            GROUP BY ALL
        ),
        practice AS (
            SELECT year, driver, COUNT(*) FILTER (WHERE position = 1) AS practice_p1
            FROM practice_results
            GROUP BY ALL
        )
        SELECT
            r.year,
            r.driver,
            r.wins,
            r.podiums,
            COALESCE(q.poles, 0) AS poles,
            COALESCE(p.practice_p1, 0) AS practice_p1
        FROM race r
        LEFT JOIN quali q USING (year, driver)
        LEFT JOIN practice p USING (year, driver)
    """
    return _run(query), query


@st.cache_data(ttl=3600)
def get_pole_conversion():
    query = """
        WITH pole AS (
            SELECT
                q.driver,
                COUNT(*) AS poles,
                COUNT(*) FILTER (WHERE r.position = 1) AS converted
            FROM quali_results q
            JOIN race_results r ON r.year = q.year AND r.round = q.round AND r.driver = q.driver
            WHERE q.position = 1
            GROUP BY q.driver
        ),
        wins AS (
            SELECT
                driver,
                COUNT(*) AS wins,
                COUNT(*) FILTER (WHERE grid_position IN (1, 2)) AS front_row_wins
            FROM race_results
            WHERE position = 1
            GROUP BY driver
        )
        SELECT
            COALESCE(p.driver, w.driver) AS driver,
            COALESCE(p.poles, 0) AS poles,
            COALESCE(p.converted, 0) AS converted,
            COALESCE(w.wins, 0) AS wins,
            COALESCE(w.front_row_wins, 0) AS front_row_wins
        FROM pole p
        FULL OUTER JOIN wins w ON p.driver = w.driver
        ORDER BY poles DESC, wins DESC
    """
    return _run(query), query


@st.cache_data(ttl=3600)
def get_wins_by_grid():
    query = """
        SELECT driver, grid_position, COUNT(*) AS wins
        FROM race_results
        WHERE position = 1
        GROUP BY ALL
        ORDER BY driver, grid_position
    """
    return _run(query), query


@st.cache_data(ttl=3600)
def get_fp3_pole_conversion():
    query = """
        SELECT
            p.driver,
            COUNT(*) AS fp3_tops,
            COUNT(*) FILTER (WHERE q.position = 1) AS poles
        FROM practice_results p
        JOIN quali_results q ON q.year = p.year AND q.round = p.round AND q.driver = p.driver
        WHERE p.session = 'FP3' AND p.position = 1
        GROUP BY p.driver
        ORDER BY fp3_tops DESC
    """
    return _run(query), query


@st.cache_data(ttl=3600)
def get_grid_drops(year: int):
    query = """
        SELECT
            r.driver,
            ARG_MAX(r.team_name, r.round) AS team_name,
            COUNT(*) AS races,
            COUNT(*) FILTER (WHERE r.grid_position > q.position OR r.grid_position = 0) AS dropped,
            ROUND(100.0 * dropped / races, 1) AS dropped_pct
        FROM race_results r
        JOIN quali_results q ON q.year = r.year AND q.round = r.round AND q.driver = r.driver
        WHERE r.year = $year
        GROUP BY r.driver
        ORDER BY dropped_pct DESC, races DESC
    """
    return _run(query, {"year": year}), query


@st.cache_data(ttl=3600)
def get_grid_drops_by_season():
    query = """
        SELECT
            r.year,
            ROUND(100.0 * COUNT(*) FILTER (WHERE r.grid_position > q.position OR r.grid_position = 0) / COUNT(*), 1) AS dropped_pct
        FROM race_results r
        JOIN quali_results q ON q.year = r.year AND q.round = r.round AND q.driver = r.driver
        GROUP BY r.year
        ORDER BY r.year
    """
    return _run(query), query


@st.cache_data(ttl=3600)
def get_reliability(year: int):
    query = """
        SELECT
            driver,
            ARG_MAX(team_name, round) AS team_name,
            COUNT(*) FILTER (WHERE classified_position = 'R') AS retirements,
            COUNT(*) FILTER (WHERE classified_position NOT IN ('R', 'D', 'W')) AS finished,
            ROUND(100.0 * finished / NULLIF(finished + retirements, 0), 1) AS completion_pct
        FROM race_results
        WHERE year = $year AND classified_position IS NOT NULL
        GROUP BY driver
        ORDER BY completion_pct DESC, finished DESC
    """
    return _run(query, {"year": year}), query


@st.cache_data(ttl=3600)
def get_retirement_causes(year: int):
    query = """
        SELECT
            team_name,
            CASE
                WHEN lower(status) IN ('accident', 'collision', 'collision damage', 'spun off', 'damage', 'debris', 'puncture') THEN 'Incident'
                WHEN lower(status) = 'retired' THEN 'Unspecified'
                ELSE 'Technical'
            END AS cause,
            COUNT(*) AS retirements
        FROM race_results
        WHERE year = $year AND classified_position = 'R'
        GROUP BY ALL
        ORDER BY team_name
    """
    return _run(query, {"year": year}), query


@st.cache_data(ttl=3600)
def get_teammate_battles(year: int):
    query = """
        WITH rr AS (
            SELECT round, driver, team_name, position, grid_position, classified_position, points
            FROM race_results
            WHERE year = $year
        ),
        pairs AS (
            SELECT
                a.round, a.team_name, a.driver AS d1, b.driver AS d2,
                a.position AS p1, b.position AS p2,
                CASE WHEN a.grid_position = 0 THEN 20 ELSE a.grid_position END AS g1,
                CASE WHEN b.grid_position = 0 THEN 20 ELSE b.grid_position END AS g2,
                a.classified_position NOT IN ('R', 'D', 'W') AS ok1,
                b.classified_position NOT IN ('R', 'D', 'W') AS ok2,
                a.points AS pts1, b.points AS pts2
            FROM rr a
            JOIN rr b ON a.round = b.round AND a.team_name = b.team_name AND a.driver < b.driver
        ),
        q AS (
            SELECT round, driver, position, q1, q2, q3 FROM quali_results WHERE year = $year
        ),
        joined AS (
            SELECT
                p.*,
                qa.position AS qp1,
                qb.position AS qp2,
                qa.q3 IS NOT NULL AS q3_1,
                qb.q3 IS NOT NULL AS q3_2,
                CASE
                    WHEN qa.q3 IS NOT NULL AND qb.q3 IS NOT NULL THEN qa.q3 - qb.q3
                    WHEN qa.q2 IS NOT NULL AND qb.q2 IS NOT NULL THEN qa.q2 - qb.q2
                    WHEN qa.q1 IS NOT NULL AND qb.q1 IS NOT NULL THEN qa.q1 - qb.q1
                END AS quali_gap
            FROM pairs p
            LEFT JOIN q qa ON qa.round = p.round AND qa.driver = p.d1
            LEFT JOIN q qb ON qb.round = p.round AND qb.driver = p.d2
        )
        SELECT
            team_name,
            d1,
            d2,
            COUNT(*) AS rounds,
            COUNT(*) FILTER (WHERE qp1 < qp2) AS quali_d1,
            COUNT(*) FILTER (WHERE qp2 < qp1) AS quali_d2,
            COUNT(*) FILTER (WHERE ok1 AND ok2 AND p1 < p2) AS race_d1,
            COUNT(*) FILTER (WHERE ok1 AND ok2 AND p2 < p1) AS race_d2,
            SUM(pts1) AS points_d1,
            SUM(pts2) AS points_d2,
            ROUND(MEDIAN(quali_gap), 3) AS median_gap_s,
            ROUND(100.0 * COUNT(*) FILTER (WHERE q3_1) / COUNT(*), 0) AS q3_pct_d1,
            ROUND(100.0 * COUNT(*) FILTER (WHERE q3_2) / COUNT(*), 0) AS q3_pct_d2,
            ROUND(AVG(g1 - p1) FILTER (WHERE ok1), 1) AS gained_d1,
            ROUND(AVG(g2 - p2) FILTER (WHERE ok2), 1) AS gained_d2
        FROM joined
        GROUP BY ALL
        ORDER BY team_name, rounds DESC
    """
    return _run(query, {"year": year}), query


@st.cache_data(ttl=3600)
def get_circuit_history(location: str):
    query = """
        SELECT
            r.year,
            r.event_name,
            w.driver AS winner,
            w.team_name AS winner_team,
            w.grid_position AS winner_grid,
            q.driver AS pole,
            (
                SELECT COUNT(*)
                FROM race_results x
                WHERE x.year = r.year AND x.round = r.round AND x.classified_position = 'R'
            ) AS dnfs
        FROM races r
        JOIN race_results w ON w.year = r.year AND w.round = r.round AND w.position = 1
        LEFT JOIN quali_results q ON q.year = r.year AND q.round = r.round AND q.position = 1
        WHERE r.location = $location
        ORDER BY r.year DESC
    """
    return _run(query, {"location": location}), query


@st.cache_data(ttl=3600)
def get_overtaking_by_year():
    query = """
        SELECT
            r.location,
            r.year,
            ROUND(AVG(ABS(CASE WHEN rr.grid_position = 0 THEN 20 ELSE rr.grid_position END - rr.position)), 2) AS positions_changed
        FROM race_results rr
        JOIN races r ON r.year = rr.year AND r.round = rr.round
        WHERE rr.classified_position NOT IN ('R', 'D', 'W')
        GROUP BY ALL
        ORDER BY r.location, r.year
    """
    return _run(query), query


@st.cache_data(ttl=3600)
def get_practice_toppers(year: int):
    query = """
        SELECT driver, session, COUNT(*) AS tops
        FROM practice_results
        WHERE year = $year AND position = 1
        GROUP BY ALL
        ORDER BY driver, session
    """
    return _run(query, {"year": year}), query


@st.cache_data(ttl=3600)
def get_sprint_summary(year: int):
    query = """
        SELECT
            driver,
            ARG_MAX(team_name, round) AS team_name,
            COUNT(*) AS sprints,
            COUNT(*) FILTER (WHERE position = 1) AS wins,
            COUNT(*) FILTER (WHERE position <= 3) AS podiums,
            SUM(points) AS points
        FROM sprint_results
        WHERE year = $year
        GROUP BY driver
        HAVING SUM(points) > 0
        ORDER BY points DESC, wins DESC
    """
    return _run(query, {"year": year}), query


@st.cache_data(ttl=3600)
def get_data_coverage():
    query = """
        SELECT 'races' AS table_name, year, COUNT(*) AS row_count FROM races GROUP BY ALL
        UNION ALL SELECT 'race_results', year, COUNT(*) FROM race_results GROUP BY ALL
        UNION ALL SELECT 'quali_results', year, COUNT(*) FROM quali_results GROUP BY ALL
        UNION ALL SELECT 'practice_results', year, COUNT(*) FROM practice_results GROUP BY ALL
        UNION ALL SELECT 'sprint_results', year, COUNT(*) FROM sprint_results GROUP BY ALL
        UNION ALL SELECT 'drivers', year, COUNT(*) FROM drivers GROUP BY ALL
        ORDER BY table_name, year
    """
    return _run(query), query

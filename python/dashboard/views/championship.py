import streamlit as st

from python.dashboard import data_layer as dl
from python.dashboard.components import charts as ch
from python.dashboard.components import ui

PLOT = {"displayModeBar": False}
season = st.session_state["season"]

standings, standings_query = dl.get_driver_standings(season)
constructors, constructors_query = dl.get_constructor_standings(season)

ui.page_header("Season", "Championship", "Standings, points trajectory and the era's dominant names.", [f"{season}"])

col_d, col_c = st.columns([1.25, 1], gap="medium")
with col_d:
    with ui.card("driver_standings", "Drivers", "Standings"):
        ui.driver_standings(standings)
        ui.sql(standings_query)

with col_c:
    with ui.card("constructor_standings", "Constructors", "Standings"):
        st.plotly_chart(ch.make_constructor_bars(constructors), config=PLOT)
        ui.sql(constructors_query)

    team_prog, team_prog_query = dl.get_points_progression(season, by="team")
    with ui.card("constructor_prog", "Constructors", "Points trajectory"):
        names = constructors["team_name"].head(5).tolist()
        st.plotly_chart(
            ch.make_points_progression(team_prog, {n: n for n in names}, names, height=360),
            config=PLOT,
        )
        ui.sql(team_prog_query)

era, era_query = dl.get_era_leaderboard()
with ui.card("era", "2022 – present", "Era dominance", "Counts per season for the most successful drivers."):
    metric = st.segmented_control(
        "Metric",
        ["Wins", "Poles", "Podiums", "Practice P1"],
        default="Wins",
        key="era_metric",
        label_visibility="collapsed",
    ) or "Wins"
    column = {"Wins": "wins", "Poles": "poles", "Podiums": "podiums", "Practice P1": "practice_p1"}[metric]
    st.plotly_chart(ch.make_era_heatmap(era, column), config=PLOT)
    ui.sql(era_query)

import streamlit as st

from python.dashboard import data_layer as dl
from python.dashboard.components import charts as ch
from python.dashboard.components import ui

PLOT = {"displayModeBar": False}
season = st.session_state["season"]

ui.page_header("Analysis", "Practice & Sprints", "Friday pace, Saturday sprints and how the track evolves.", [f"{season}"])

evo, evo_query = dl.get_weekend_evolution(season)
with ui.card("evolution", "Track evolution", "FP1 → qualifying", "How much faster the field was in qualifying than in FP1."):
    if evo.empty:
        ui.empty("No practice data for this season yet.")
    else:
        st.plotly_chart(ch.make_track_evolution(evo), config=PLOT)
    ui.sql(evo_query)

col_a, col_b = st.columns(2, gap="medium")
with col_a:
    toppers, toppers_query = dl.get_practice_toppers(season)
    with ui.card("practice", "Practice", "Session toppers"):
        if toppers.empty:
            ui.empty("No practice sessions yet.")
        else:
            st.plotly_chart(ch.make_practice_toppers(toppers), config=PLOT)
        ui.sql(toppers_query)
with col_b:
    sprints, sprints_query = dl.get_sprint_summary(season)
    with ui.card("sprints", "Sprints", "Sprint points"):
        if sprints.empty:
            ui.empty("No sprint races this season.")
        else:
            st.plotly_chart(
                ch.make_team_bars(
                    sprints, "driver", "points", "team_name",
                    [f"{p:g} pts · {w}W" for p, w in zip(sprints["points"], sprints["wins"])],
                    "<b>%{y}</b> %{x:g} pts<extra>%{customdata[0]}</extra>",
                ),
                config=PLOT,
            )
        ui.sql(sprints_query)

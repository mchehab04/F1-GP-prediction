import streamlit as st

from python.dashboard import data_layer as dl
from python.dashboard.components import charts as ch
from python.dashboard.components import ui

PLOT = {"displayModeBar": False}
season = st.session_state["season"]

ui.page_header("Analysis", "Teammates", "The only fair fight: same car, same weekend.", [f"{season}"])

battles, battles_query = dl.get_teammate_battles(season)
main = battles[battles["rounds"] >= 3]
short = battles[battles["rounds"] < 3]

if main.empty:
    ui.empty("Not enough races yet this season.")
else:
    cols = st.columns(2, gap="medium")
    for i, r in enumerate(main.itertuples()):
        with cols[i % 2]:
            ui.garage_card(r)
    if not short.empty:
        pairs = ", ".join(f"{r.d1}/{r.d2} ({r.team_name}, {r.rounds})" for r in short.itertuples())
        ui.html(f'<div class="footnote">Short pairings not shown: {pairs}</div>')
    ui.sql(battles_query)

quali_gap, quali_gap_query = dl.get_teammate_quali_gaps(season)
with ui.card("quali", "Qualifying", "Median gap", "One-lap delta between teammates across the season."):
    st.plotly_chart(ch.make_quali_gap_dumbbell(quali_gap), config=PLOT)
    ui.sql(quali_gap_query)

import streamlit as st

from python.dashboard import data_layer as dl
from python.dashboard.components import charts as ch
from python.dashboard.components import ui

PLOT = {"displayModeBar": False}
season = st.session_state["season"]

calendar_df, _ = dl.get_season_calendar(season)
done = calendar_df[calendar_df["winner"].notna()]

ui.page_header("Season", "Race Explorer", "Pick a Grand Prix to replay grid, result and qualifying.", [f"{season}"])

if done.empty:
    ui.empty("No races have been run this season yet.")
    st.stop()

labels = {int(r.round): f"R{r.round} · {r.event_name}" for r in done.itertuples()}
round_no = st.selectbox("Grand Prix", list(labels)[::-1], format_func=labels.get, key=f"race_{season}")
event = done[done["round"] == round_no].iloc[0]

results, results_query = dl.get_race_results(season, round_no)
quali, quali_query = dl.get_quali_results(season, round_no)

classified = results[~results["classified_position"].isin(["R", "D", "W"])].copy()
classified["start"] = classified["grid_position"].replace(0, 20)
classified["gained"] = classified["start"] - classified["position"]
mover = classified.sort_values("gained", ascending=False).iloc[0] if not classified.empty else None

ui.stat_tiles([
    {"label": "Winner", "value": event["winner"], "note": f"from P{int(event['winner_grid'])}", "color": dl.get_team_color(event["winner_team"])},
    {"label": "Pole", "value": event["pole"] or "–", "note": "converted" if event["pole"] == event["winner"] else "not converted"},
    {"label": "Biggest climb", "value": mover["driver"] if mover is not None else "–", "note": f"+{int(mover['gained'])} places" if mover is not None else ""},
    {"label": "Retirements", "value": int((results["classified_position"] == "R").sum()), "note": event["location"]},
])

col_slope, col_table = st.columns([1.1, 1], gap="medium")
with col_slope:
    with ui.card("slope", "Race", "Grid to flag"):
        st.plotly_chart(ch.make_slope_chart(results), config=PLOT)
with col_table:
    with ui.card("classification", "Race", "Classification"):
        ui.classification(results)
        ui.sql(results_query)

with ui.card("quali_gaps", "Qualifying", "Gap to pole", "Best lap across Q1–Q3."):
    st.plotly_chart(ch.make_quali_gap_bars(quali), config=PLOT)
    ui.sql(quali_query)

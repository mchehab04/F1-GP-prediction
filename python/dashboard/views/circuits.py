import streamlit as st

from python.dashboard import data_layer as dl
from python.dashboard.components import charts as ch
from python.dashboard.components import ui

PLOT = {"displayModeBar": False}

ui.page_header("Analysis", "Circuits", "Every venue's character: chaos, overtaking and who wins there.", ["All seasons"])

circuit_df, circuit_query = dl.get_circuit_dna()

with ui.card("dna", "Circuit DNA", "Chaos vs. overtaking", "Colour shows how often pole converts to a win."):
    st.plotly_chart(ch.make_circuit_dna_scatter(circuit_df), config=PLOT)
    ui.sql(circuit_query)

with ui.card("guide", "Circuit guide", "Track history"):
    locations = sorted(circuit_df["location"].tolist())
    default = locations.index("Monza") if "Monza" in locations else 0
    location = st.selectbox("Circuit", locations, index=default, key="circuit_pick")
    info = circuit_df[circuit_df["location"] == location].iloc[0]
    history, history_query = dl.get_circuit_history(location)
    ui.stat_tiles([
        {"label": "Grand Prix", "value": info["event_name"].replace(" Grand Prix", ""), "note": f"{len(history)} races since 2022"},
        {"label": "DNFs per race", "value": f"{info['avg_dnfs']:.1f}"},
        {"label": "Places changed", "value": f"{info['overtaking_index']:.1f}", "note": "per classified driver"},
        {"label": "Pole → win", "value": f"{info['pole_to_win_pct']:.0f}%"},
    ])
    ui.circuit_history(history)
    ui.sql(history_query)

overtaking, overtaking_query = dl.get_overtaking_by_year()
with ui.card("overtaking", "Overtaking", "Places changed by season", "Average positions gained or lost per classified driver."):
    st.plotly_chart(ch.make_overtaking_heatmap(overtaking), config=PLOT)
    ui.sql(overtaking_query)

import streamlit as st

from python.dashboard import data_layer as dl
from python.dashboard.components import ui
from python.dashboard.components.predictor import render_predictor_widget

season = st.session_state["season"]

ui.page_header("Model", "Race Predictor", "A rules-based projection from grid slot, season form and circuit history.", [f"{season}", "Heuristic · pre-ML"])

circuit_df, _ = dl.get_circuit_dna()
render_predictor_widget(dl.get_drivers_for_year(season), circuit_df, dl.get_driver_form(season))

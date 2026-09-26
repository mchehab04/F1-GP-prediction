import streamlit as st

from python.dashboard import data_layer as dl
from python.dashboard.components import charts as ch
from python.dashboard.components import ui

PLOT = {"displayModeBar": False}

ui.page_header("Model", "Methodology", "Where the numbers come from.")

with ui.card("pipeline", "Under the hood", "Data pipeline"):
    ui.pipeline()

coverage, coverage_query = dl.get_data_coverage()
with ui.card("coverage", "Data", "Rows per table and season"):
    st.plotly_chart(ch.make_coverage_heatmap(coverage), config=PLOT)
    ui.sql(coverage_query)

with ui.card("definitions", "Definitions", "How metrics are counted"):
    ui.html("""
        <dl class="defs">
            <dt>Clean race</dt><dd>Both teammates classified; retirements, DSQ and DNS excluded.</dd>
            <dt>Places changed</dt><dd>Absolute difference between grid and finish; pit-lane starts count as P20.</dd>
            <dt>Grid drop</dt><dd>Started behind qualifying position, or from the pit lane.</dd>
            <dt>Points</dt><dd>Race plus sprint points.</dd>
            <dt>Pole</dt><dd>Fastest in qualifying, before any grid penalties.</dd>
        </dl>
    """)

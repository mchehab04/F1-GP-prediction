import os
import sys

import streamlit as st

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from python.dashboard.data_layer import get_seasons
from python.dashboard.components import ui

st.set_page_config(
    page_title="Grid to Flag · F1 Analytics",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="auto",
)

SECTIONS = {
    "Season": [
        st.Page("views/race_hub.py", title="Race Hub", url_path="hub", default=True),
        st.Page("views/championship.py", title="Championship", url_path="championship"),
        st.Page("views/race_explorer.py", title="Race Explorer", url_path="races"),
    ],
    "Analysis": [
        st.Page("views/qualifying.py", title="Qualifying & Grid", url_path="qualifying"),
        st.Page("views/teammates.py", title="Teammates", url_path="teammates"),
        st.Page("views/circuits.py", title="Circuits", url_path="circuits"),
        st.Page("views/race_weekend.py", title="Practice & Sprints", url_path="weekend"),
        st.Page("views/reliability.py", title="Reliability", url_path="reliability"),
    ],
    "Model": [
        st.Page("views/predictor.py", title="Race Predictor", url_path="predictor"),
        st.Page("views/methodology.py", title="Methodology", url_path="methodology"),
    ],
}

page = st.navigation(SECTIONS, position="hidden")

ui.inject_styles()
ui.active_nav(page.url_path or "hub")
if not st.session_state.get("intro_played"):
    st.session_state["intro_played"] = True
    ui.lights_out_intro()

seasons = get_seasons()
if st.session_state.get("season") not in seasons:
    st.session_state["season"] = seasons[0]

with st.sidebar:
    ui.sidebar_brand()
    st.selectbox("Season", seasons, key="season")
    for section, pages in SECTIONS.items():
        ui.nav_heading(section)
        for p in pages:
            with st.container(key=f"nav_{p.url_path or 'hub'}"):
                st.page_link(p)
    ui.sidebar_footer()

page.run()
ui.footer()

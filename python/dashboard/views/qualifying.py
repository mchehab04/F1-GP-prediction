import streamlit as st

from python.dashboard import data_layer as dl
from python.dashboard.components import charts as ch
from python.dashboard.components import ui

PLOT = {"displayModeBar": False}

ui.page_header("Analysis", "Qualifying & Grid", "How much Saturday decides Sunday.", ["All seasons"])

grid_conv, grid_conv_query = dl.get_grid_win_conversion()
poles, poles_query = dl.get_pole_conversion()
fp3, fp3_query = dl.get_fp3_pole_conversion()
wins_grid, wins_grid_query = dl.get_wins_by_grid()

front = poles["front_row_wins"].sum()
total_wins = poles["wins"].sum()
pole_total = poles["poles"].sum()
pole_hits = poles["converted"].sum()
p1 = grid_conv[grid_conv["grid_position"] == 1]
ui.stat_tiles([
    {"label": "Pole → win", "value": f"{round(pole_hits * 100 / pole_total) if pole_total else 0}%", "note": f"{pole_hits} of {pole_total} poles"},
    {"label": "Wins from front row", "value": f"{round(front * 100 / total_wins) if total_wins else 0}%", "note": f"{front} of {total_wins} wins"},
    {"label": "P1 → podium", "value": f"{p1['podium_rate_pct'].iloc[0]:.0f}%" if not p1.empty else "–", "note": "starting from pole"},
    {"label": "Winning slots", "value": wins_grid["grid_position"].nunique(), "note": f"deepest win from P{wins_grid['grid_position'].max()}"},
])

with ui.card("conversion", "Grid", "What each grid slot is worth", "Share of starts that ended in a win, podium or points."):
    st.plotly_chart(ch.make_grid_conversion_chart(grid_conv), config=PLOT)
    ui.sql(grid_conv_query)

col_a, col_b = st.columns(2, gap="medium")
with col_a:
    with ui.card("pole_conv", "Pole position", "Poles converted to wins"):
        st.plotly_chart(ch.make_conversion_bars(poles, "driver", "poles", "converted", "Poles", "Wins from pole"), config=PLOT)
        ui.sql(poles_query)
with col_b:
    with ui.card("fp3_conv", "Final practice", "FP3 pace → pole", "Times the FP3 leader went on to take pole."):
        st.plotly_chart(ch.make_conversion_bars(fp3, "driver", "fp3_tops", "poles", "FP3 tops", "Poles"), config=PLOT)
        ui.sql(fp3_query)

with ui.card("wins_grid", "Race wins", "Where winners started", "Every win of the era by starting slot."):
    st.plotly_chart(ch.make_wins_by_grid_heatmap(wins_grid), config=PLOT)
    ui.sql(wins_grid_query)

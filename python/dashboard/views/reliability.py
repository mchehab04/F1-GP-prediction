import streamlit as st

from python.dashboard import data_layer as dl
from python.dashboard.components import charts as ch
from python.dashboard.components import ui

PLOT = {"displayModeBar": False}
season = st.session_state["season"]

ui.page_header("Analysis", "Reliability", "Retirements, their causes and grid drops.", [f"{season}"])

rel, rel_query = dl.get_reliability(season)
causes, causes_query = dl.get_retirement_causes(season)
drops, drops_query = dl.get_grid_drops(season)
drops_era, drops_era_query = dl.get_grid_drops_by_season()

finished = int(rel["finished"].sum())
retired = int(rel["retirements"].sum())
perfect = rel[(rel["retirements"] == 0) & (rel["finished"] >= 5)]
ui.stat_tiles([
    {"label": "Retirements", "value": retired, "note": f"{season}"},
    {"label": "Finish rate", "value": f"{round(finished * 100 / (finished + retired)) if finished + retired else 0}%", "note": "classified starts"},
    {"label": "Never retired", "value": len(perfect), "note": ", ".join(perfect["driver"].head(4)) or "–"},
    {"label": "Started behind quali slot", "value": f"{drops_era.loc[drops_era['year'] == season, 'dropped_pct'].iloc[0]:.1f}%" if season in drops_era["year"].values else "–", "note": "grid drops"},
])

col_a, col_b = st.columns(2, gap="medium")
with col_a:
    with ui.card("completion", "Drivers", "Finish rate"):
        rows = rel[rel["finished"] + rel["retirements"] >= 3].sort_values(["completion_pct", "finished"], ascending=[True, True])
        rows = rows.iloc[::-1]
        st.plotly_chart(
            ch.make_team_bars(
                rows, "driver", "completion_pct", "team_name",
                [f"{p:.0f}% · {r} DNF" for p, r in zip(rows["completion_pct"], rows["retirements"])],
                "<b>%{y}</b> %{x:.1f}%<extra>%{customdata[0]}</extra>",
                suffix="%", xmax=125,
            ),
            config=PLOT,
        )
        ui.sql(rel_query)
with col_b:
    with ui.card("causes", "Teams", "Retirements by team", "Hover for incident vs. technical split where FastF1 records a cause."):
        if causes.empty:
            ui.empty("No retirements this season.")
        else:
            st.plotly_chart(ch.make_retirement_causes(causes), config=PLOT)
        ui.sql(causes_query)

col_c, col_d = st.columns([1.3, 1], gap="medium")
with col_c:
    with ui.card("drops", "Grid drops", "Started behind qualifying slot", "Penalties, pit-lane starts and other grid changes."):
        rows = drops[drops["dropped"] > 0]
        if rows.empty:
            ui.empty("No grid drops this season.")
        else:
            st.plotly_chart(
                ch.make_team_bars(
                    rows, "driver", "dropped_pct", "team_name",
                    [f"{d} of {r}" for d, r in zip(rows["dropped"], rows["races"])],
                    "<b>%{y}</b> %{x:.1f}% of races<extra>%{customdata[0]}</extra>",
                    suffix="%", limit=12,
                ),
                config=PLOT,
            )
        ui.sql(drops_query)
with col_d:
    with ui.card("drops_era", "Grid drops", "By season"):
        st.plotly_chart(ch.make_single_bars([str(y) for y in drops_era["year"]], drops_era["dropped_pct"].tolist(), suffix="%"), config=PLOT)
        ui.sql(drops_era_query)

import streamlit as st

from python.dashboard import data_layer as dl
from python.dashboard.components import charts as ch
from python.dashboard.components import ui

PLOT = {"displayModeBar": False}
season = st.session_state["season"]

calendar_df, calendar_query = dl.get_season_calendar(season)
standings, _ = dl.get_driver_standings(season)
constructors, _ = dl.get_constructor_standings(season)

done = calendar_df[calendar_df["winner"].notna()]
rounds_total = len(calendar_df)
rounds_done = len(done)
upcoming = calendar_df[calendar_df["winner"].isna()]
status = "Season complete" if upcoming.empty else f"Next: {upcoming.iloc[0]['event_name']}"
converted = int((done["winner"] == done["pole"]).sum())
pole_pct = round(converted * 100 / rounds_done) if rounds_done else 0

with st.container(key="hero"):
    ui.html(f"""
        <div class="eyebrow">{ui.DOTS}Race hub &middot; Round {rounds_done} of {rounds_total}</div>
        <div class="hero-title">{season} <span>Season</span></div>
        <p class="hero-sub">{status}</p>
    """)
    ui.timing_tower([
        (rounds_done, "Races run"),
        (done["winner"].nunique(), "Different winners"),
        (pole_pct, "Won from pole", "%"),
        (int(standings["dnfs"].sum()) if not standings.empty else 0, "Retirements"),
    ])

col_lead, col_last, col_team = st.columns([1, 1.15, 1], gap="medium")

with col_lead:
    with ui.card("leader", "Drivers' championship", "Leader"):
        if standings.empty:
            ui.empty("No races yet.")
        else:
            lead = standings.iloc[0]
            gap = lead["points"] - standings.iloc[1]["points"] if len(standings) > 1 else 0
            ui.spotlight(
                lead["driver"], lead["team_name"], f"{lead['points']:g}", "points",
                [(f"+{gap:g}", f"over {standings.iloc[1]['driver']}"), (str(lead["wins"]), "wins"), (str(lead["poles"]), "poles")],
            )

with col_last:
    if rounds_done:
        last = done.iloc[-1]
        results, _ = dl.get_race_results(season, int(last["round"]))
        with ui.card("last_race", f"Latest race · R{int(last['round'])}", last["event_name"]):
            ui.podium(
                [{"pos": int(r.position), "driver": r.driver, "team": r.team_name} for r in results.head(3).itertuples()],
                caption=f"Pole: {last['pole']} &middot; winner started P{int(last['winner_grid'])}",
            )

with col_team:
    with ui.card("constructor_lead", "Constructors' championship", "Leader"):
        if constructors.empty:
            ui.empty("No races yet.")
        else:
            lead = constructors.iloc[0]
            gap = lead["points"] - constructors.iloc[1]["points"] if len(constructors) > 1 else 0
            ui.spotlight(
                lead["team_name"].upper(), f"{lead['podiums']} podiums", f"{lead['points']:g}", "points",
                [(f"+{gap:g}", f"over {constructors.iloc[1]['team_name']}"), (str(lead["wins"]), "wins"), (str(lead["dnfs"]), "DNFs")],
            )

progression, progression_query = dl.get_points_progression(season)
top = standings.head(6)
with ui.card("battle", "Championship battle", "Top six, round by round", "Race and sprint points combined."):
    st.plotly_chart(
        ch.make_points_progression(progression, dict(zip(standings["driver"], standings["team_name"])), top["driver"].tolist()),
        config=PLOT,
    )
    ui.sql(progression_query)

with ui.card("calendar", "Calendar", f"{season} rounds", "Winner and starting slot for every Grand Prix."):
    ui.calendar(calendar_df)
    ui.sql(calendar_query)

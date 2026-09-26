import streamlit as st
import pandas as pd
from python.dashboard.data_layer import get_team_color
from python.dashboard.components.ui import card, html

def calculate_race_prediction(driver: str, team: str, grid_pos: int, track_chaos: float, overtaking_idx: float, pole_conv: float, driver_avg_finish: float) -> dict:
    historical_win_base = {1: 58.0, 2: 21.0, 3: 11.0, 4: 5.0, 5: 3.0, 6: 1.0}.get(grid_pos, 0.2)
    historical_podium_base = {1: 85.0, 2: 70.0, 3: 55.0, 4: 35.0, 5: 25.0, 6: 15.0, 7: 8.0, 8: 5.0}.get(grid_pos, max(1.0, 20.0 - grid_pos * 1.5))
    historical_points_base = max(5.0, min(96.0, 100.0 - (grid_pos - 1) * 6.5))
    
    overtaking_factor = (overtaking_idx - 2.5) / 5.0
    chaos_penalty = min(0.35, track_chaos * 0.05)
    
    if grid_pos == 1:
        win_prob = max(10.0, min(92.0, pole_conv * 0.7 + historical_win_base * 0.3 - (chaos_penalty * 20)))
    else:
        grid_delta = (grid_pos - 1) * 4.0
        win_prob = max(0.1, historical_win_base + (overtaking_factor * 2.0) - (grid_delta * 0.2))
        
    podium_prob = max(win_prob, min(95.0, historical_podium_base + (overtaking_factor * 8.0) - (chaos_penalty * 15.0)))
    points_prob = max(podium_prob, min(99.0, historical_points_base + (overtaking_factor * 5.0) - (chaos_penalty * 10.0)))
    
    driver_bias = (driver_avg_finish - 10.0) * 0.2 if driver_avg_finish > 0 else 0
    predicted_finish = max(1.0, min(20.0, float(grid_pos) + driver_bias - (overtaking_factor * 1.2)))
    
    expected_change = grid_pos - predicted_finish
    
    return {
        "predicted_finish": round(predicted_finish, 1),
        "expected_change": round(expected_change, 1),
        "win_prob": round(win_prob, 1),
        "podium_prob": round(podium_prob, 1),
        "points_prob": round(points_prob, 1),
        "dnf_risk": round(track_chaos * 6.5, 1)
    }

def _starting_grid(grid_slot: int, finish_slot: int, code: str) -> str:
    slots = []
    for pos in range(1, 21):
        row = 1 if pos % 2 else 2
        col = 2 + ((pos + 1) // 2 - 1) * 2 + (0 if pos % 2 else 1)
        classes = ["slot"]
        tag = ""
        if pos == grid_slot:
            classes.append("grid")
            tag = f"<em>{code}</em>"
        if pos == finish_slot:
            classes.append("finish")
            if not tag:
                tag = "<em>FIN</em>"
        slots.append(
            f'<div class="{" ".join(classes)}" style="grid-row:{row};grid-column:{col} / span 2"><span>P{pos}</span>{tag}</div>'
        )
    return (
        '<div class="grid-wrap"><div class="grid-strip"><div class="start-line"></div>'
        + "".join(slots)
        + "</div></div>"
    )


def render_predictor_widget(drivers_df: pd.DataFrame, circuit_df: pd.DataFrame, form_df: pd.DataFrame):
    col_setup, col_result = st.columns([5, 7], gap="large")

    with col_setup:
        with card("setup", "Race setup", "Build the weekend"):
            all_drivers = sorted(drivers_df["driver"].unique().tolist())
            leader = form_df["driver"].iloc[0] if not form_df.empty else None
            default_driver = all_drivers.index(leader) if leader in all_drivers else 0
            selected_driver = st.selectbox("Driver", all_drivers, index=default_driver if all_drivers else None)

            driver_row = drivers_df[drivers_df["driver"] == selected_driver]
            team_name = driver_row["team_name"].values[0] if not driver_row.empty else "Unknown Team"
            driver_number = driver_row["driver_number"].values[0] if not driver_row.empty else ""
            team_color = get_team_color(team_name)

            driver_form_row = form_df[form_df["driver"] == selected_driver] if not form_df.empty else pd.DataFrame()
            avg_finish = driver_form_row["avg_finish"].values[0] if not driver_form_row.empty else 10.0

            track_locations = sorted(circuit_df["location"].tolist()) if not circuit_df.empty else ["Monza", "Silverstone", "Spa"]
            selected_track = st.selectbox("Circuit", track_locations, index=0)

            track_info = circuit_df[circuit_df["location"] == selected_track]
            track_chaos = track_info["avg_dnfs"].values[0] if not track_info.empty else 2.5
            overtaking_idx = track_info["overtaking_index"].values[0] if not track_info.empty else 2.8
            pole_conv = track_info["pole_to_win_pct"].values[0] if not track_info.empty else 55.0

            grid_slot = st.slider("Grid slot", min_value=1, max_value=20, value=1, step=1, format="P%d")

            html(f"""
                <div class="driver-card" style="--team:{team_color}">
                    <div class="num">{driver_number}</div>
                    <div><div class="code">{selected_driver}</div><div class="team">{team_name}</div></div>
                    <div class="stats">
                        <div><b>P{avg_finish:.1f}</b><span>Season avg</span></div>
                        <div><b>{pole_conv:.0f}%</b><span>Pole → win</span></div>
                    </div>
                </div>
            """)

    res = calculate_race_prediction(selected_driver, team_name, grid_slot, track_chaos, overtaking_idx, pole_conv, avg_finish)
    change = res["expected_change"]
    if change > 0:
        delta = f'<span class="delta up">▲ {change:.1f}</span> from grid P{grid_slot}'
    elif change < 0:
        delta = f'<span class="delta down">▼ {abs(change):.1f}</span> from grid P{grid_slot}'
    else:
        delta = f'<span class="delta flat">＝</span> holds grid P{grid_slot}'

    def prob_bar(label: str, pct: float, color_var: str) -> str:
        return (
            f'<div class="prob" style="--c:var({color_var});--w:{pct}%">'
            f'<div class="prob-top"><span>{label}</span><b>{pct:.1f}%</b></div>'
            f'<div class="track"><div class="fill"></div></div></div>'
        )

    with col_result:
        with card("projection", "Projection", f"{selected_driver} at {selected_track}"):
            html(f"""
                <div class="result-top" style="--team:{team_color}">
                    <div class="readout pos">
                        <div class="label">Projected finish</div>
                        <div class="big"><small>P</small>{res['predicted_finish']}</div>
                        <div class="note">{delta}</div>
                    </div>
                    <div class="readout">
                        <div class="label">DNF risk</div>
                        <div class="big">{res['dnf_risk']}<small>%</small></div>
                        <div class="note">{track_chaos:.1f} DNFs per race here</div>
                    </div>
                </div>
            """)
            html(
                prob_bar("Win", res["win_prob"], "--win")
                + prob_bar("Podium", res["podium_prob"], "--podium")
                + prob_bar("Points", res["points_prob"], "--points")
            )

    finish_slot = int(min(20, max(1, round(res["predicted_finish"]))))
    with card("grid", "Starting grid", "Where they line up, and where they're projected to finish"):
        html(f"""
            <div style="--team:{team_color}">
                {_starting_grid(grid_slot, finish_slot, selected_driver)}
                <div class="grid-legend"><span><i class="g"></i>Grid slot</span><span><i class="f"></i>Projected finish</span></div>
            </div>
        """)

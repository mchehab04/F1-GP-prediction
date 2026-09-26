import plotly.graph_objects as go
import pandas as pd
from python.dashboard.data_layer import get_team_color

INK = "#F2F3F5"
INK_2 = "#A9ABB6"
INK_3 = "#6C6F7C"
GRID = "rgba(255,255,255,0.06)"
RED = "#E10600"
WIN = "#A463F2"
PODIUM = "#12A86A"
POINTS = "#3B82F6"
FONT = "Titillium Web, Segoe UI, system-ui, sans-serif"
MONO = "JetBrains Mono, ui-monospace, monospace"


def _axis_title(text: str) -> dict:
    return dict(text=text, font=dict(size=12, color=INK_3))


def apply_f1_theme(fig: go.Figure, height: int = 400, **kwargs) -> go.Figure:
    layout_args = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": dict(family=FONT, color=INK_2, size=13),
        "margin": dict(l=10, r=20, t=30, b=20),
        "height": height,
        "hoverlabel": dict(
            bgcolor="#1B1C23",
            bordercolor="rgba(255,255,255,0.16)",
            font=dict(family=FONT, color=INK, size=13),
        ),
        "legend": dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=12, color=INK_2),
        ),
    }
    layout_args.update(kwargs)
    fig.update_layout(**layout_args)
    fig.update_xaxes(gridcolor=GRID, zerolinecolor="rgba(255,255,255,0.14)", linecolor="rgba(0,0,0,0)", tickfont=dict(size=12, color=INK_3))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor="rgba(255,255,255,0.14)", linecolor="rgba(0,0,0,0)", tickfont=dict(size=12, color=INK_2))
    return fig


def _pair_label(row) -> str:
    return f"<b>{row.d1}</b>  v  <b>{row.d2}</b><br><span style='font-size:11px;color:{INK_3}'>{row.team_name}</span>"


def make_tug_of_war_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig

    rows = df.sort_values(by=["team_name", "total_clean_races"], ascending=[True, False])
    labels = [_pair_label(r) for r in rows.itertuples()]
    colors = [get_team_color(t) for t in rows["team_name"]]

    fig.add_trace(go.Bar(
        y=labels,
        x=-rows["d1_wins"],
        orientation="h",
        marker=dict(color=colors, cornerradius=4),
        text=rows["d1_wins"],
        textposition="outside",
        textfont=dict(family=MONO, color=INK, size=12),
        cliponaxis=False,
        hovertemplate=[f"<b>{r.d1}</b> ahead in {r.d1_wins} of {r.total_clean_races}<extra>{r.team_name}</extra>" for r in rows.itertuples()],
    ))
    fig.add_trace(go.Bar(
        y=labels,
        x=rows["d2_wins"],
        orientation="h",
        marker=dict(color=colors, opacity=0.55, cornerradius=4),
        text=rows["d2_wins"],
        textposition="outside",
        textfont=dict(family=MONO, color=INK, size=12),
        cliponaxis=False,
        hovertemplate=[f"<b>{r.d2}</b> ahead in {r.d2_wins} of {r.total_clean_races}<extra>{r.team_name}</extra>" for r in rows.itertuples()],
    ))

    peak = int(max(rows["d1_wins"].max(), rows["d2_wins"].max(), 5))
    step = 5 if peak <= 20 else 10
    ticks = list(range(-((peak // step) * step), (peak // step) * step + 1, step))

    apply_f1_theme(
        fig,
        height=max(380, len(rows) * 46 + 60),
        barmode="relative",
        bargap=0.38,
        showlegend=False,
        xaxis=dict(
            range=[-peak * 1.18, peak * 1.18],
            tickvals=ticks,
            ticktext=[str(abs(t)) for t in ticks],
            title=_axis_title("Races finished ahead of teammate"),
            showgrid=True,
        ),
        yaxis=dict(autorange="reversed", showgrid=False),
    )
    fig.add_vline(x=0, line_width=2, line_color=RED)
    return fig


def make_quali_gap_dumbbell(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig

    rows = df.assign(x=-df["median_gap_s"]).sort_values(by="x")
    labels = [_pair_label(r) for r in rows.itertuples()]
    colors = [get_team_color(t) for t in rows["team_name"]]

    stem_x, stem_y = [], []
    for label, x in zip(labels, rows["x"]):
        stem_x += [0, x, None]
        stem_y += [label, label, None]
    fig.add_trace(go.Scatter(x=stem_x, y=stem_y, mode="lines", line=dict(color="rgba(255,255,255,0.18)", width=2), hoverinfo="skip"))

    fig.add_trace(go.Scatter(
        x=rows["x"],
        y=labels,
        mode="markers",
        marker=dict(size=13, color=colors, line=dict(color="#0B0C10", width=2)),
        hovertemplate=[
            f"<b>{r.d1 if r.median_gap_s > 0 else r.d2}</b> faster by {abs(r.median_gap_s):.3f}s"
            f"<br><span style='color:{INK_3}'>median of {r.sessions_counted} sessions</span><extra>{r.team_name}</extra>"
            for r in rows.itertuples()
        ],
    ))

    reach = max(float(rows["x"].abs().max()), 0.1) * 1.15
    apply_f1_theme(
        fig,
        height=max(380, len(rows) * 46 + 60),
        showlegend=False,
        xaxis=dict(range=[-reach, reach], title=_axis_title("Median qualifying gap (s)"), zeroline=False, tickformat="+.2f"),
        yaxis=dict(autorange="reversed", showgrid=False),
    )
    fig.add_vline(x=0, line_width=2, line_color=RED)
    fig.add_annotation(x=0, xref="x", y=1.0, yref="paper", yanchor="bottom", xanchor="right", xshift=-10, text="◀ LEFT DRIVER FASTER", showarrow=False, font=dict(size=11, color=INK_3))
    fig.add_annotation(x=0, xref="x", y=1.0, yref="paper", yanchor="bottom", xanchor="left", xshift=10, text="RIGHT DRIVER FASTER ▶", showarrow=False, font=dict(size=11, color=INK_3))
    return fig


def make_circuit_dna_scatter(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig

    median_dnf = df["avg_dnfs"].median()
    median_moves = df["overtaking_index"].median()
    spread = ((df["avg_dnfs"] - median_dnf) / df["avg_dnfs"].std()) ** 2 + ((df["overtaking_index"] - median_moves) / df["overtaking_index"].std()) ** 2
    labelled = set(spread.nlargest(8).index)

    fig.add_hline(y=median_moves, line_width=1, line_dash="dot", line_color="rgba(255,255,255,0.18)")
    fig.add_vline(x=median_dnf, line_width=1, line_dash="dot", line_color="rgba(255,255,255,0.18)")

    fig.add_trace(go.Scatter(
        x=df["avg_dnfs"],
        y=df["overtaking_index"],
        mode="markers+text",
        text=[loc if i in labelled else "" for i, loc in zip(df.index, df["location"])],
        textposition="top center",
        textfont=dict(size=12, color=INK_2),
        marker=dict(
            size=14,
            color=df["pole_to_win_pct"],
            cmin=0,
            cmax=100,
            colorscale=[[0, "#5A2A27"], [0.5, "#A3231B"], [1, "#FF3B2F"]],
            line=dict(color="#0B0C10", width=2),
            colorbar=dict(
                title=dict(text="Pole → win %", font=dict(size=11, color=INK_3), side="right"),
                thickness=8,
                len=0.6,
                outlinewidth=0,
                tickfont=dict(size=11, color=INK_3),
            ),
        ),
        customdata=df[["event_name", "pole_to_win_pct"]],
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "DNFs / race: %{x:.2f}<br>"
            "Positions changed / driver: %{y:.2f}<br>"
            "Pole → win: %{customdata[1]:.0f}%<extra></extra>"
        ),
    ))

    corner = dict(xref="paper", yref="paper", showarrow=False, font=dict(size=11, color=INK_3))
    fig.add_annotation(x=0.01, y=0.99, xanchor="left", yanchor="top", text="CLEAN · OVERTAKING", **corner)
    fig.add_annotation(x=0.97, y=0.99, xanchor="right", yanchor="top", text="CHAOTIC · OVERTAKING", **corner)
    fig.add_annotation(x=0.01, y=0.01, xanchor="left", yanchor="bottom", text="CLEAN · PROCESSIONAL", **corner)
    fig.add_annotation(x=0.97, y=0.01, xanchor="right", yanchor="bottom", text="CHAOTIC · PROCESSIONAL", **corner)

    apply_f1_theme(
        fig,
        height=540,
        showlegend=False,
        xaxis=dict(title=_axis_title("DNFs per race"), zeroline=False),
        yaxis=dict(title=_axis_title("Positions changed per driver"), zeroline=False),
    )
    return fig


def make_grid_conversion_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig

    for col, name, color in [
        ("points_rate_pct", "Points", POINTS),
        ("podium_rate_pct", "Podium", PODIUM),
        ("win_rate_pct", "Win", WIN),
    ]:
        fig.add_trace(go.Bar(
            x=df["grid_position"],
            y=df[col],
            name=name,
            marker=dict(color=color, cornerradius=3),
            hovertemplate=f"{name}: %{{y:.1f}}%<extra></extra>",
        ))

    apply_f1_theme(
        fig,
        height=400,
        barmode="group",
        bargap=0.28,
        bargroupgap=0.08,
        hovermode="x unified",
        xaxis=dict(title=_axis_title("Grid slot"), tickmode="array", tickvals=df["grid_position"], ticktext=[f"P{p}" for p in df["grid_position"]], showgrid=False),
        yaxis=dict(title=_axis_title("Share of starts (%)"), range=[0, 102], ticksuffix="%"),
        legend=dict(traceorder="reversed", orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def make_weekend_evolution_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig

    sessions = [
        ("fp1_avg_s", "FP1", "#4A4D59", 2),
        ("fp2_avg_s", "FP2", "#7C7F8C", 2),
        ("fp3_avg_s", "FP3", "#B9BBC4", 2),
        ("quali_avg_s", "Qualifying", RED, 3),
    ]
    for col, name, color, width in sessions:
        if col not in df.columns:
            continue
        fig.add_trace(go.Scatter(
            x=df["location"],
            y=df[col],
            name=name,
            mode="lines+markers",
            line=dict(color=color, width=width),
            marker=dict(size=8, color=color, line=dict(color="#0B0C10", width=2)),
            hovertemplate=f"{name}: %{{y:.3f}}s<extra></extra>",
        ))

    apply_f1_theme(
        fig,
        height=440,
        hovermode="x unified",
        xaxis=dict(tickangle=-40, showgrid=False),
        yaxis=dict(title=_axis_title("Average best lap (s)")),
    )
    return fig


SEQ_RED = [[0, "#1F1A1E"], [0.001, "#4A1D1B"], [0.5, "#A3231B"], [1, "#FF3B2F"]]
SEQ_RED_SOLID = [[0, "#4A1D1B"], [0.5, "#A3231B"], [1, "#FF3B2F"]]
SESSION_RAMP = {"FP1": "#4A4D59", "FP2": "#7C7F8C", "FP3": "#B9BBC4"}
CAUSE_COLORS = {"Incident": "#E06A2B", "Technical": "#3B82F6", "Unspecified": "#6C6F7C"}


def _dashes_by_team(names: list[str], teams: dict[str, str]) -> dict[str, str]:
    seen: dict[str, int] = {}
    out = {}
    for n in names:
        t = teams.get(n, "")
        out[n] = "solid" if seen.get(t, 0) == 0 else "dot"
        seen[t] = seen.get(t, 0) + 1
    return out


def make_points_progression(df: pd.DataFrame, teams: dict[str, str], names: list[str], height: int = 420) -> go.Figure:
    fig = go.Figure()
    if df.empty or not names:
        return fig
    dashes = _dashes_by_team(names, teams)
    last_round = df["round"].max()
    for name in names:
        d = df[df["name"] == name]
        color = get_team_color(teams.get(name, name))
        fig.add_trace(go.Scatter(
            x=d["round"],
            y=d["cum_points"],
            name=name,
            mode="lines",
            line=dict(color=color, width=2.5, dash=dashes[name], shape="spline", smoothing=0.3),
            hovertemplate=f"<b>{name}</b> %{{y:g}} pts<extra></extra>",
        ))
        end = d[d["round"] == last_round]
        fig.add_trace(go.Scatter(
            x=end["round"],
            y=end["cum_points"],
            mode="markers",
            marker=dict(size=8, color=color, line=dict(color="#0B0C10", width=2)),
            hoverinfo="skip",
            showlegend=False,
            cliponaxis=False,
        ))
    finals = df[(df["round"] == last_round) & (df["name"].isin(names))].sort_values("cum_points", ascending=False)
    min_gap = max(df["cum_points"].max(), 1) * 0.055
    placed = []
    for r in finals.itertuples():
        y = r.cum_points
        if placed and placed[-1] - y < min_gap:
            y = placed[-1] - min_gap
        placed.append(y)
        fig.add_annotation(
            x=last_round, y=y, text=r.name, xanchor="left", xshift=10, showarrow=False,
            font=dict(family=FONT, size=12, color=INK),
        )
    apply_f1_theme(
        fig,
        height=height,
        hovermode="x unified",
        margin=dict(l=10, r=110, t=30, b=20),
        xaxis=dict(title=_axis_title("Round"), dtick=1, showgrid=False, range=[0.8, last_round + 0.2]),
        yaxis=dict(title=_axis_title("Points")),
    )
    return fig


def make_constructor_bars(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig
    rows = df.sort_values("points")
    fig.add_trace(go.Bar(
        x=rows["points"],
        y=rows["team_name"],
        orientation="h",
        marker=dict(color=[get_team_color(t) for t in rows["team_name"]], cornerradius=3),
        text=[f"{p:g}" for p in rows["points"]],
        textposition="outside",
        textfont=dict(family=MONO, size=12, color=INK),
        cliponaxis=False,
        customdata=rows[["wins", "podiums"]],
        hovertemplate="<b>%{y}</b><br>%{x:g} pts · %{customdata[0]} wins · %{customdata[1]} podiums<extra></extra>",
    ))
    apply_f1_theme(
        fig,
        height=max(300, len(rows) * 36 + 40),
        showlegend=False,
        bargap=0.35,
        margin=dict(l=10, r=50, t=10, b=10),
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False),
    )
    return fig


def make_era_heatmap(df: pd.DataFrame, metric: str, limit: int = 14) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig
    pivot = df.pivot_table(index="driver", columns="year", values=metric, aggfunc="sum", fill_value=0)
    pivot = pivot[pivot.sum(axis=1) > 0]
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index].head(limit)
    if pivot.empty:
        return fig
    totals = pivot.sum(axis=1)
    labels = [f"<b>{d}</b>  <span style='color:{INK_3}'>{int(totals[d])}</span>" for d in pivot.index]
    text = [["" if v == 0 else str(int(v)) for v in row] for row in pivot.values]
    fig.add_trace(go.Heatmap(
        z=pivot.values,
        x=[str(c) for c in pivot.columns],
        y=labels,
        text=text,
        texttemplate="%{text}",
        textfont=dict(family=MONO, size=13, color=INK),
        colorscale=SEQ_RED,
        zmin=0,
        showscale=False,
        xgap=3,
        ygap=3,
        hovertemplate="%{x}: %{z}<extra></extra>",
    ))
    apply_f1_theme(
        fig,
        height=max(320, len(pivot) * 34 + 60),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(side="top", showgrid=False, tickfont=dict(size=13, color=INK_2)),
        yaxis=dict(autorange="reversed", showgrid=False),
    )
    return fig


def make_conversion_bars(df: pd.DataFrame, name_col: str, total_col: str, hit_col: str, total_label: str, hit_label: str, limit: int = 12) -> go.Figure:
    fig = go.Figure()
    rows = df[df[total_col] > 0].sort_values(total_col, ascending=False).head(limit).iloc[::-1]
    if rows.empty:
        return fig
    pct = (rows[hit_col] * 100 / rows[total_col]).round(0)
    fig.add_trace(go.Bar(
        x=rows[total_col], y=rows[name_col], orientation="h", name=total_label,
        marker=dict(color="#34353E", cornerradius=3),
        text=[f"{h}/{t} · {p:.0f}%" for h, t, p in zip(rows[hit_col], rows[total_col], pct)],
        textposition="outside",
        textfont=dict(family=MONO, size=11, color=INK_2),
        cliponaxis=False,
        hovertemplate=f"%{{y}}: %{{x}} {total_label.lower()}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=rows[hit_col], y=rows[name_col], orientation="h", name=hit_label,
        marker=dict(color=RED, cornerradius=3),
        hovertemplate=f"%{{y}}: %{{x}} {hit_label.lower()}<extra></extra>",
    ))
    peak = rows[total_col].max()
    apply_f1_theme(
        fig,
        height=max(300, len(rows) * 32 + 70),
        barmode="overlay",
        bargap=0.3,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(range=[0, peak * 1.45], showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False),
    )
    return fig


def make_wins_by_grid_heatmap(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig
    slots = sorted(df["grid_position"].unique(), key=lambda g: (g == 0, g))
    slot_labels = ["PL" if g == 0 else f"P{g}" for g in slots]
    totals = df.groupby("driver")["wins"].sum().sort_values(ascending=False)
    pivot = df.pivot_table(index="driver", columns="grid_position", values="wins", aggfunc="sum", fill_value=0).reindex(index=totals.index, columns=slots, fill_value=0)
    text = [["" if v == 0 else str(int(v)) for v in row] for row in pivot.values]
    fig.add_trace(go.Heatmap(
        z=pivot.values,
        x=slot_labels,
        y=[f"<b>{d}</b>  <span style='color:{INK_3}'>{int(totals[d])}</span>" for d in pivot.index],
        text=text,
        texttemplate="%{text}",
        textfont=dict(family=MONO, size=12, color=INK),
        colorscale=SEQ_RED,
        zmin=0,
        showscale=False,
        xgap=3,
        ygap=3,
        hovertemplate="From %{x}: %{z} wins<extra></extra>",
    ))
    apply_f1_theme(
        fig,
        height=max(300, len(pivot) * 34 + 70),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(side="top", showgrid=False, type="category", title=_axis_title("Starting slot")),
        yaxis=dict(autorange="reversed", showgrid=False),
    )
    return fig


def make_team_bars(df: pd.DataFrame, name_col: str, value_col: str, team_col: str, text: list[str], hover: str, suffix: str = "", limit: int | None = None, xmax: float | None = None) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig
    rows = df.head(limit) if limit else df
    rows = rows.iloc[::-1]
    text = list(reversed(text[: len(rows)]))
    fig.add_trace(go.Bar(
        x=rows[value_col],
        y=rows[name_col],
        orientation="h",
        marker=dict(color=[get_team_color(t) for t in rows[team_col]], cornerradius=3),
        text=text,
        textposition="outside",
        textfont=dict(family=MONO, size=11, color=INK_2),
        cliponaxis=False,
        customdata=rows[[team_col]],
        hovertemplate=hover,
    ))
    peak = xmax if xmax is not None else rows[value_col].max() * 1.25
    apply_f1_theme(
        fig,
        height=max(300, len(rows) * 28 + 50),
        showlegend=False,
        bargap=0.3,
        margin=dict(l=10, r=60, t=10, b=10),
        xaxis=dict(range=[0, peak], showgrid=True, ticksuffix=suffix, zeroline=False),
        yaxis=dict(showgrid=False),
    )
    return fig


def make_retirement_causes(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig
    pivot = df.pivot_table(index="team_name", columns="cause", values="retirements", aggfunc="sum", fill_value=0)
    for cause in CAUSE_COLORS:
        if cause not in pivot.columns:
            pivot[cause] = 0
    pivot["total"] = pivot[list(CAUSE_COLORS)].sum(axis=1)
    pivot = pivot.sort_values("total")
    fig.add_trace(go.Bar(
        x=pivot["total"],
        y=pivot.index,
        orientation="h",
        marker=dict(color=[get_team_color(t) for t in pivot.index], cornerradius=3),
        text=[f"{int(t)}" for t in pivot["total"]],
        textposition="outside",
        textfont=dict(family=MONO, size=12, color=INK),
        cliponaxis=False,
        customdata=pivot[list(CAUSE_COLORS)].values,
        hovertemplate="<b>%{y}</b> %{x} retirements<br>Incident %{customdata[0]} · Technical %{customdata[1]} · Unspecified %{customdata[2]}<extra></extra>",
    ))
    apply_f1_theme(
        fig,
        height=max(300, len(pivot) * 32 + 40),
        showlegend=False,
        bargap=0.35,
        margin=dict(l=10, r=40, t=10, b=10),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False),
    )
    return fig


def make_slope_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig
    n = len(df)
    dnf_y = n + 1.5
    teams = dict(zip(df["driver"], df["team_name"]))
    dashes = _dashes_by_team(df.sort_values("position")["driver"].tolist(), teams)
    for r in df.itertuples():
        start = 20 if r.grid_position == 0 else r.grid_position
        out = r.classified_position in ("R", "D", "W")
        end = dnf_y if out else r.position
        color = get_team_color(r.team_name)
        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[start, end],
            mode="lines+markers",
            line=dict(color=color, width=2.5, dash=dashes[r.driver]),
            marker=dict(size=9, color=color, line=dict(color="#0B0C10", width=2)),
            opacity=0.35 if out else 1,
            hovertemplate=f"<b>{r.driver}</b> P{start} → {'DNF' if out else 'P' + str(r.position)}<extra>{r.team_name}</extra>",
            showlegend=False,
        ))
        fig.add_annotation(x=0, y=start, text=f"{r.driver}", xanchor="right", xshift=-12, showarrow=False, font=dict(family=MONO, size=11, color=INK_2))
        if not out:
            fig.add_annotation(x=1, y=end, text=f"{r.driver}", xanchor="left", xshift=12, showarrow=False, font=dict(family=MONO, size=11, color=INK))
    fig.add_annotation(x=1, y=dnf_y, text="DNF", xanchor="left", xshift=12, showarrow=False, font=dict(family=MONO, size=11, color=INK_3))
    apply_f1_theme(
        fig,
        height=640,
        margin=dict(l=60, r=60, t=40, b=10),
        xaxis=dict(range=[-0.25, 1.25], tickvals=[0, 1], ticktext=["GRID", "FINISH"], side="top", showgrid=False, tickfont=dict(size=12, color=INK_2)),
        yaxis=dict(autorange="reversed", showticklabels=False, showgrid=False, zeroline=False, range=[dnf_y + 0.8, 0.2]),
    )
    return fig


def make_quali_gap_bars(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    rows = df[df["best"] < 999].copy()
    if rows.empty:
        return fig
    pole = rows["best"].min()
    rows["gap"] = rows["best"] - pole
    rows = rows.sort_values("position").iloc[::-1]
    fig.add_trace(go.Bar(
        x=rows["gap"],
        y=[f"P{p}  {d}" for p, d in zip(rows["position"], rows["driver"])],
        orientation="h",
        marker=dict(color=[get_team_color(t) for t in rows["team_name"]], cornerradius=3),
        text=["POLE" if g == 0 else f"+{g:.3f}" for g in rows["gap"]],
        textposition="outside",
        textfont=dict(family=MONO, size=11, color=INK_2),
        cliponaxis=False,
        hovertemplate="%{y}: +%{x:.3f}s<extra></extra>",
    ))
    apply_f1_theme(
        fig,
        height=max(360, len(rows) * 26 + 40),
        showlegend=False,
        bargap=0.3,
        margin=dict(l=10, r=70, t=10, b=10),
        xaxis=dict(title=_axis_title("Gap to pole (s)"), zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(family=MONO, size=11, color=INK_2)),
    )
    return fig


def make_overtaking_heatmap(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig
    pivot = df.pivot_table(index="location", columns="year", values="positions_changed")
    pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]
    text = [["" if pd.isna(v) else f"{v:.1f}" for v in row] for row in pivot.values]
    fig.add_trace(go.Heatmap(
        z=pivot.values,
        x=[str(c) for c in pivot.columns],
        y=pivot.index.tolist(),
        text=text,
        texttemplate="%{text}",
        textfont=dict(family=MONO, size=11, color=INK),
        colorscale=SEQ_RED_SOLID,
        showscale=False,
        xgap=3,
        ygap=3,
        hoverongaps=False,
        hovertemplate="%{y} %{x}: %{z:.2f} places<extra></extra>",
    ))
    apply_f1_theme(
        fig,
        height=max(360, len(pivot) * 26 + 60),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(side="top", showgrid=False, tickfont=dict(size=13, color=INK_2)),
        yaxis=dict(autorange="reversed", showgrid=False),
    )
    return fig


def make_track_evolution(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig
    rows = df.dropna(subset=["fp1_avg_s", "quali_avg_s"]).copy()
    rows["gain"] = rows["fp1_avg_s"] - rows["quali_avg_s"]
    fig.add_trace(go.Bar(
        x=[f"R{r} {l}" for r, l in zip(rows["round"], rows["location"])],
        y=rows["gain"],
        marker=dict(color=rows["gain"], colorscale=SEQ_RED_SOLID, cornerradius=3),
        customdata=rows[["fp1_avg_s", "quali_avg_s"]],
        hovertemplate="<b>%{x}</b><br>FP1 %{customdata[0]:.3f}s → Q %{customdata[1]:.3f}s<br>%{y:.2f}s faster<extra></extra>",
    ))
    apply_f1_theme(
        fig,
        height=400,
        showlegend=False,
        bargap=0.25,
        xaxis=dict(tickangle=-40, showgrid=False),
        yaxis=dict(title=_axis_title("Seconds faster, FP1 → qualifying"), ticksuffix="s"),
    )
    return fig


def make_practice_toppers(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig
    order = df.groupby("driver")["tops"].sum().sort_values().index.tolist()
    for session, color in SESSION_RAMP.items():
        d = df[df["session"] == session].set_index("driver")["tops"].reindex(order, fill_value=0)
        fig.add_trace(go.Bar(
            x=d.values, y=order, orientation="h", name=session,
            marker=dict(color=color, line=dict(color="#14151B", width=2)),
            hovertemplate=f"{session}: %{{x}}<extra>%{{y}}</extra>",
        ))
    apply_f1_theme(
        fig,
        height=max(300, len(order) * 30 + 60),
        barmode="stack",
        bargap=0.3,
        margin=dict(l=10, r=20, t=40, b=10),
        xaxis=dict(title=_axis_title("Sessions topped")),
        yaxis=dict(showgrid=False),
        legend=dict(traceorder="normal", orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def make_single_bars(x: list, y: list, suffix: str = "", color: str = RED, height: int = 300) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=x, y=y,
        marker=dict(color=color, cornerradius=3),
        text=[f"{v:g}{suffix}" for v in y],
        textposition="outside",
        textfont=dict(family=MONO, size=12, color=INK),
        cliponaxis=False,
        hovertemplate=f"%{{x}}: %{{y:g}}{suffix}<extra></extra>",
    ))
    apply_f1_theme(
        fig,
        height=height,
        showlegend=False,
        bargap=0.45,
        xaxis=dict(type="category", showgrid=False),
        yaxis=dict(ticksuffix=suffix, range=[0, max(y) * 1.25 if y else 1]),
    )
    return fig


def make_coverage_heatmap(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig
    pivot = df.pivot_table(index="table_name", columns="year", values="row_count", fill_value=0)
    fig.add_trace(go.Heatmap(
        z=pivot.div(pivot.max(axis=1), axis=0).values,
        customdata=pivot.values,
        x=[str(c) for c in pivot.columns],
        y=pivot.index.tolist(),
        text=[[f"{int(v):,}" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(family=MONO, size=12, color=INK),
        colorscale=SEQ_RED_SOLID,
        showscale=False,
        xgap=3,
        ygap=3,
        hovertemplate="%{y} %{x}: %{customdata:,} rows<extra></extra>",
    ))
    apply_f1_theme(
        fig,
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(side="top", showgrid=False),
        yaxis=dict(showgrid=False, tickfont=dict(family=MONO, size=12, color=INK_2)),
    )
    return fig

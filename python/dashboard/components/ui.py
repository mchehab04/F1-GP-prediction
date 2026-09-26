import os
from contextlib import contextmanager
from html import escape

import pandas as pd
import streamlit as st

from python.dashboard.data_layer import get_team_color

STYLES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles.css")
DOTS = '<span class="dots"><i></i><i></i><i></i><i></i><i></i></span>'


def html(markup: str):
    st.html("".join(line.strip() for line in markup.splitlines()))


def inject_styles():
    with open(STYLES_PATH, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def lights_out_intro():
    pods = "".join(f'<div class="pod"><i style="--i:{i}"></i><i style="--i:{i}"></i></div>' for i in range(5))
    html(f"""
        <div class="lights-out" aria-hidden="true">
            <div class="gantry">{pods}</div>
            <div class="lo-text">LIGHTS OUT</div>
        </div>
    """)
    st.markdown(
        "<style>[data-testid='stMainBlockContainer'],[data-testid='stSidebarContent']"
        "{animation:rise .8s cubic-bezier(.2,.8,.2,1) 2.6s both}</style>",
        unsafe_allow_html=True,
    )


def sidebar_brand():
    html(f"""
        <div class="brand">
            {DOTS}
            <div class="brand-name">Grid <span>to</span> Flag</div>
            <div class="brand-sub">F1 analytics &middot; ground-effect era</div>
        </div>
    """)


def active_nav(url_path: str):
    st.markdown(
        f"<style>.st-key-nav_{url_path} a{{background:rgba(225,6,0,.12)!important}}"
        f".st-key-nav_{url_path} a::before{{transform:scaleY(1)!important}}"
        f".st-key-nav_{url_path} a p{{color:var(--ink)!important}}</style>",
        unsafe_allow_html=True,
    )


def nav_heading(text: str):
    html(f'<div class="nav-h">{escape(text)}</div>')


def sidebar_footer():
    html('<div class="side-foot"><div class="checker"></div><p>Data via FastF1</p></div>')


def footer():
    html("""
        <div class="site-foot">
            <div class="checker"></div>
            <p>Data via FastF1 &middot; DuckDB &middot; Streamlit</p>
        </div>
    """)


def page_header(kicker: str, title: str, sub: str = "", chips: list[str] | None = None):
    chip_html = "".join(f'<span class="chip">{c}</span>' for c in (chips or []))
    sub_html = f'<p class="page-sub">{sub}</p>' if sub else ""
    html(f"""
        <div class="page-head">
            <div class="eyebrow">{DOTS}{kicker}</div>
            <div class="page-title">{title}</div>
            {sub_html}
            <div class="chips-row">{chip_html}</div>
        </div>
    """)


def timing_tower(stats: list[tuple], animate: bool = True):
    cells = []
    for item in stats:
        value, label = item[0], item[1]
        suffix = item[2] if len(item) > 2 else ""
        if animate and isinstance(value, (int,)) and not isinstance(value, bool):
            num = f'<b class="count" style="--to:{value}" data-suffix="{suffix}"></b>'
        else:
            num = f"<b>{value}{suffix}</b>"
        cells.append(f"<div>{num}<span>{label}</span></div>")
    html(f'<div class="tower">{"".join(cells)}</div><div class="checker"></div>')


def card_head(kicker: str, title: str, sub: str = ""):
    sub_html = f'<div class="card-sub">{sub}</div>' if sub else ""
    html(f'<div class="card-head"><div class="kicker">{kicker}</div><div class="card-title">{title}</div>{sub_html}</div>')


@contextmanager
def card(key: str, kicker: str, title: str, sub: str = ""):
    with st.container(border=True, key=f"card_{key}"):
        card_head(kicker, title, sub)
        yield


def sql(query: str):
    with st.expander("SQL"):
        st.code(query.strip(), language="sql")


def empty(text: str):
    html(f'<div class="empty">{text}</div>')


def stat_tiles(items: list[dict]):
    tiles = []
    for it in items:
        accent = it.get("color", "var(--red)")
        note = f'<span class="t-note">{it["note"]}</span>' if it.get("note") else ""
        tiles.append(
            f'<div class="tile" style="--accent:{accent}"><span class="t-label">{it["label"]}</span>'
            f'<b>{it["value"]}</b>{note}</div>'
        )
    html(f'<div class="tiles">{"".join(tiles)}</div>')


def spotlight(code: str, team: str, value: str, value_label: str, stats: list[tuple[str, str]]):
    color = get_team_color(team)
    stat_html = "".join(f"<div><b>{v}</b><span>{l}</span></div>" for v, l in stats)
    html(f"""
        <div class="spotlight" style="--team:{color}">
            <div class="sp-top">
                <div>
                    <div class="sp-code">{escape(code)}</div>
                    <div class="sp-team">{escape(team)}</div>
                </div>
                <div class="sp-value"><b>{value}</b><span>{value_label}</span></div>
            </div>
            <div class="sp-stats">{stat_html}</div>
        </div>
    """)


def podium(rows: list[dict], caption: str = ""):
    order = {2: 0, 1: 1, 3: 2}
    steps = sorted(rows[:3], key=lambda r: order.get(r["pos"], 9))
    blocks = []
    for r in steps:
        color = get_team_color(r["team"])
        blocks.append(f"""
            <div class="step p{r['pos']}" style="--team:{color}">
                <div class="st-code">{escape(r['driver'])}</div>
                <div class="st-team">{escape(r['team'])}</div>
                <div class="st-block"><span>{r['pos']}</span></div>
            </div>
        """)
    cap = f'<div class="podium-cap">{caption}</div>' if caption else ""
    html(f'<div class="podium">{"".join(blocks)}</div>{cap}')


def driver_standings(df: pd.DataFrame):
    if df.empty:
        empty("No results yet.")
        return
    leader = df["points"].iloc[0]
    rows = []
    for i, r in enumerate(df.itertuples()):
        color = get_team_color(r.team_name)
        gap = "LEADER" if i == 0 else f"-{leader - r.points:g}"
        rows.append(f"""
            <div class="tt-row" style="--team:{color};--d:{i * 28}ms">
                <span class="tt-pos">{r.pos}</span>
                <span class="tt-name"><b>{escape(r.driver)}</b><small>{escape(r.team_name)}</small></span>
                <span class="tt-pts">{r.points:g}</span>
                <span class="tt-gap">{gap}</span>
                <span class="tt-n">{r.wins}</span>
                <span class="tt-n">{r.podiums}</span>
                <span class="tt-n">{r.poles}</span>
                <span class="tt-n">{r.dnfs}</span>
            </div>
        """)
    html(f"""
        <div class="tt">
            <div class="tt-row tt-headrow">
                <span>Pos</span><span>Driver</span><span class="r">Pts</span><span class="r">Gap</span>
                <span class="r">Wins</span><span class="r">Pod</span><span class="r">Poles</span><span class="r">DNF</span>
            </div>
            {''.join(rows)}
        </div>
    """)


def calendar(df: pd.DataFrame):
    chips = []
    next_marked = False
    for i, r in enumerate(df.itertuples()):
        sprint = '<em class="cal-sprint">SPRINT</em>' if r.sprint_included else ""
        if isinstance(r.winner, str):
            color = get_team_color(r.winner_team)
            body = f'<div class="cal-win" style="--team:{color}"><b>{r.winner}</b><small>P{int(r.winner_grid) if r.winner_grid else "L"} start</small></div>'
            state = "done"
        else:
            state = "upcoming" if next_marked else "next"
            next_marked = True
            body = f'<div class="cal-win empty-win"><b>{"NEXT" if state == "next" else "—"}</b></div>'
        chips.append(f"""
            <div class="cal {state}" style="--d:{i * 22}ms">
                <div class="cal-top"><span>R{r.round}</span>{sprint}</div>
                <div class="cal-loc">{escape(r.location)}</div>
                {body}
            </div>
        """)
    html(f'<div class="calendar">{"".join(chips)}</div>')


def classification(df: pd.DataFrame):
    rows = []
    for i, r in enumerate(df.itertuples()):
        color = get_team_color(r.team_name)
        grid = "PL" if r.grid_position == 0 else r.grid_position
        classified = r.classified_position not in ("R", "D", "W")
        if classified:
            start = 20 if r.grid_position == 0 else r.grid_position
            moved = start - r.position
            delta = f'<span class="delta up">▲{moved}</span>' if moved > 0 else (f'<span class="delta down">▼{-moved}</span>' if moved < 0 else '<span class="delta flat">–</span>')
            pos = r.position
        else:
            delta = f'<span class="tag">{"DNF" if r.classified_position == "R" else ("DSQ" if r.classified_position == "D" else "DNS")}</span>'
            pos = "–"
        pts = f"+{r.points:g}" if r.points else ""
        rows.append(f"""
            <div class="cl-row{'' if classified else ' out'}" style="--team:{color};--d:{i * 22}ms">
                <span class="tt-pos">{pos}</span>
                <span class="tt-name"><b>{escape(r.driver)}</b><small>{escape(r.team_name)}</small></span>
                <span class="tt-n">{grid}</span>
                <span class="tt-n">{delta}</span>
                <span class="tt-pts">{pts}</span>
            </div>
        """)
    html(f"""
        <div class="tt cl">
            <div class="cl-row tt-headrow"><span>Pos</span><span>Driver</span><span class="r">Grid</span><span class="r">+/-</span><span class="r">Pts</span></div>
            {''.join(rows)}
        </div>
    """)


def _split(a: float, b: float) -> tuple[float, float]:
    total = a + b
    if total <= 0:
        return 50.0, 50.0
    return a * 100 / total, b * 100 / total


def garage_card(r):
    color = get_team_color(r.team_name)
    metrics = [
        ("Qualifying", r.quali_d1, r.quali_d2, "{:g}"),
        ("Race", r.race_d1, r.race_d2, "{:g}"),
        ("Points", r.points_d1, r.points_d2, "{:g}"),
        ("Q3 rate", r.q3_pct_d1, r.q3_pct_d2, "{:g}%"),
    ]
    rows = []
    for label, a, b, fmt in metrics:
        a = 0 if pd.isna(a) else a
        b = 0 if pd.isna(b) else b
        pa, pb = _split(a, b)
        la = "win" if a > b else ""
        lb = "win" if b > a else ""
        rows.append(f"""
            <div class="g-row">
                <span class="g-v {la}">{fmt.format(a)}</span>
                <div class="g-mid"><div class="g-label">{label}</div><div class="g-bar"><i style="width:{pa}%"></i><i style="width:{pb}%"></i></div></div>
                <span class="g-v r {lb}">{fmt.format(b)}</span>
            </div>
        """)
    gap = r.median_gap_s
    if pd.isna(gap) or gap == 0:
        gap_text = "Level on median qualifying pace"
    else:
        faster = r.d1 if gap < 0 else r.d2
        gap_text = f"<b>{faster}</b> faster by {abs(gap):.3f}s on median qualifying pace"
    html(f"""
        <div class="garage" style="--team:{color}">
            <div class="g-head"><span>{escape(r.team_name)}</span><span>{r.rounds} rounds together</span></div>
            <div class="g-names"><b>{escape(r.d1)}</b><i>VS</i><b>{escape(r.d2)}</b></div>
            {''.join(rows)}
            <div class="g-foot">{gap_text}</div>
        </div>
    """)


def circuit_history(df: pd.DataFrame):
    rows = []
    for i, r in enumerate(df.itertuples()):
        color = get_team_color(r.winner_team)
        grid = "PL" if r.winner_grid == 0 else f"P{r.winner_grid}"
        rows.append(f"""
            <div class="ch-row" style="--team:{color};--d:{i * 40}ms">
                <span class="ch-year">{r.year}</span>
                <span class="tt-name"><b>{escape(r.winner)}</b><small>{escape(r.winner_team)}</small></span>
                <span class="tt-n">{grid}</span>
                <span class="tt-n">{escape(str(r.pole or '–'))}</span>
                <span class="tt-n">{r.dnfs}</span>
            </div>
        """)
    html(f"""
        <div class="tt ch">
            <div class="ch-row tt-headrow"><span>Year</span><span>Winner</span><span class="r">Started</span><span class="r">Pole</span><span class="r">DNFs</span></div>
            {''.join(rows)}
        </div>
    """)


def pipeline():
    html("""
        <div class="pipeline">
            <div class="stage">
                <div class="step">01 / INGEST</div>
                <h4>FastF1</h4>
                <p>Practice, qualifying, sprint and race sessions, 2022 onward.</p>
            </div>
            <div class="link"></div>
            <div class="stage">
                <div class="step">02 / STORE</div>
                <h4>DuckDB</h4>
                <p>Cleaned classified positions; DNS and withdrawals imputed to P20.</p>
                <div class="chips"><code>races</code><code>drivers</code><code>race_results</code><code>quali_results</code><code>practice_results</code><code>sprint_results</code></div>
            </div>
            <div class="link"></div>
            <div class="stage">
                <div class="step">03 / SERVE</div>
                <h4>Streamlit</h4>
                <p>Cached read-only SQL queries rendered with Plotly.</p>
            </div>
        </div>
    """)

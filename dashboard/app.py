"""
Orbitalis Mission Control Dashboard — Production UI
Space Tech / Aerospace Enterprise Mission Control interface.

Backend logic intentionally preserved:
- AWS Athena via `run_query`
- AWS S3 object counts via boto3
- Existing Athena table names and SQL query semantics
- Existing five dashboard pages (+ a new About page, UI-only)
"""

import streamlit as st
import pandas as pd
import boto3
import plotly.graph_objects as go
from athena_client import run_query


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Orbitalis Mission Control",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ENTERPRISE MISSION-CONTROL THEME — "Deep Orbit"
# Palette moves away from black/gold toward a signal-blue /
# ion-violet space theme, closer to real tracking consoles.
# ============================================================

st.markdown(
    """
    <style>
    /* ============================================================
       ORBITALIS MISSION CONTROL — "DEEP ORBIT" THEME
       ============================================================ */

    :root {
        --bg: #060911;
        --bg-2: #0A0F1C;
        --sidebar: #04060C;
        --card: #0E1524;
        --card-2: #121B2E;
        --card-hover: #16213A;
        --border: #223050;
        --border-soft: #1A2540;

        --text: #E8ECF6;
        --text-soft: #B9C2D6;
        --muted: #6E7A96;

        --primary: #3FA9F5;      /* signal blue */
        --primary-soft: rgba(63,169,245,.10);
        --ion: #8E7CFF;          /* ion violet, secondary accent */
        --emerald: #35D7A6;
        --amber: #F2A93B;
        --coral: #F2555F;
    }

    /* ---------- App shell ---------- */

    .stApp {
        background: var(--bg);
        background-image:
            radial-gradient(1.2px 1.2px at 12% 18%, rgba(255,255,255,.6), transparent),
            radial-gradient(1px 1px at 78% 6%, rgba(255,255,255,.45), transparent),
            radial-gradient(1.6px 1.6px at 42% 55%, rgba(255,255,255,.4), transparent),
            radial-gradient(1px 1px at 92% 40%, rgba(255,255,255,.35), transparent),
            radial-gradient(1px 1px at 22% 78%, rgba(255,255,255,.4), transparent),
            radial-gradient(1.5px 1.5px at 63% 28%, rgba(255,255,255,.32), transparent),
            radial-gradient(1px 1px at 6% 50%, rgba(255,255,255,.35), transparent),
            radial-gradient(1px 1px at 96% 82%, rgba(255,255,255,.3), transparent),
            radial-gradient(ellipse 900px 520px at 85% -6%, rgba(63,169,245,.14), transparent 60%),
            radial-gradient(ellipse 750px 520px at -8% 12%, rgba(142,124,255,.10), transparent 55%),
            linear-gradient(180deg, var(--bg-2) 0%, var(--bg) 340px);
        background-size:
            600px 600px, 600px 600px, 600px 600px, 600px 600px,
            600px 600px, 600px 600px, 600px 600px, 600px 600px,
            auto, auto, auto;
        background-repeat: repeat, repeat, repeat, repeat, repeat, repeat, repeat, repeat, no-repeat, no-repeat, no-repeat;
        animation: driftStars 110s linear infinite;
        color: var(--text);
    }

    @keyframes driftStars {
        from { background-position: 0 0, 0 0, 0 0, 0 0, 0 0, 0 0, 0 0, 0 0, 0 0, 0 0, 0 0; }
        to   { background-position: -600px -300px, -600px -300px, -600px -300px, -600px -300px,
               -600px -300px, -600px -300px, -600px -300px, -600px -300px, 0 0, 0 0, 0 0; }
    }

    * { font-variant-numeric: tabular-nums; }

    .main .block-container {
        max-width: 1600px;
        padding-top: 2.2rem;
        padding-bottom: 3.5rem;
    }

    /* ---------- Typography ---------- */

    h1, h2, h3, h4, h5, h6 {
        color: var(--text) !important;
        letter-spacing: -0.02em;
    }

    h1 {
        font-size: 2.15rem !important;
        font-weight: 800 !important;
        line-height: 1.1 !important;
    }

    h2 { font-weight: 750 !important; }
    h3, h4 { font-weight: 700 !important; }

    p, label, .stCaption {
        color: var(--muted);
    }

    /* ---------- Sidebar ---------- */

    section[data-testid="stSidebar"] {
        background: var(--sidebar) !important;
        border-right: 1px solid var(--border-soft) !important;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.1rem;
    }

    section[data-testid="stSidebar"] .stMarkdown {
        color: var(--text-soft);
    }

    .brand {
        display: flex;
        align-items: center;
        gap: .6rem;
        padding: .2rem .1rem 1.1rem .1rem;
        border-bottom: 1px solid var(--border-soft);
        margin-bottom: 1rem;
    }

    .brand-mark {
        width: 34px;
        height: 34px;
        border-radius: 9px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.05rem;
        background: linear-gradient(155deg, rgba(63,169,245,.22), rgba(142,124,255,.14));
        border: 1px solid var(--border);
        flex-shrink: 0;
    }

    .brand-text { line-height: 1.25; }

    .brand-name {
        font-size: 1.02rem;
        font-weight: 700;
        letter-spacing: .01em;
        color: var(--text) !important;
    }

    .brand-sub {
        color: #4E597A !important;
        font-size: .72rem;
        margin-top: .05rem;
    }

    .system-status {
        display: flex;
        align-items: center;
        gap: .5rem;
        margin: .95rem 0 .3rem 0;
        padding: .45rem .6rem;
        border: 1px solid var(--border-soft);
        border-radius: 7px;
        background: rgba(53, 215, 166, .05);
        color: #86E6C8 !important;
        font-size: .72rem;
        font-weight: 600;
    }

    .live-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--emerald);
        animation: pulseDot 1.8s ease-out infinite;
        flex-shrink: 0;
    }

    @keyframes pulseDot {
        0%   { box-shadow: 0 0 0 0 rgba(53,215,166,.55); }
        70%  { box-shadow: 0 0 0 7px rgba(53,215,166,0); }
        100% { box-shadow: 0 0 0 0 rgba(53,215,166,0); }
    }

    .sidebar-clock {
        font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
        font-size: .7rem;
        color: var(--muted) !important;
        margin: 0 0 1.05rem 0;
        letter-spacing: .02em;
    }

    .nav-label {
        color: #4E597A !important;
        font-size: .68rem;
        font-weight: 700;
        letter-spacing: .09em;
        margin-bottom: .35rem;
    }

    div[data-testid="stRadio"] label {
        color: #C7D0E4 !important;
        font-weight: 600;
        padding: .3rem .5rem;
        border-radius: 7px;
        transition: all .15s ease;
    }

    div[data-testid="stRadio"] label:hover {
        color: var(--primary) !important;
        background: rgba(63,169,245,.07);
    }

    div[data-testid="stRadio"] [role="radiogroup"] {
        gap: .15rem;
    }

    /* ---------- Page header ---------- */

    .page-kicker {
        display: flex;
        align-items: center;
        gap: .5rem;
        margin-bottom: .6rem;
        color: var(--primary) !important;
        font-size: .74rem;
        font-weight: 600;
        font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
    }

    .page-kicker::before {
        content: "";
        width: 14px;
        height: 2px;
        background: linear-gradient(90deg, var(--primary), var(--ion));
        animation: scanBar 2.6s ease-in-out infinite;
    }

    @keyframes scanBar {
        0%, 100% { width: 6px; opacity: .5; }
        50%      { width: 20px; opacity: 1; }
    }

    .page-subtitle {
        color: var(--muted) !important;
        margin-top: -.4rem;
        margin-bottom: 1.4rem;
        font-size: .93rem;
        max-width: 66ch;
    }

    /* ---------- KPI cards ---------- */

    div[data-testid="stMetric"] {
        background: linear-gradient(160deg, var(--card-2), var(--card)) !important;
        border: 1px solid var(--border) !important;
        border-top: 3px solid var(--primary) !important;
        border-radius: 10px !important;
        padding: .95rem 1.1rem .85rem 1.1rem !important;
        min-height: 100px !important;
        box-shadow: 0 6px 18px rgba(0,0,0,.32);
        transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 26px rgba(0,0,0,.4);
    }

    div[data-testid="column"]:nth-of-type(4n+1) div[data-testid="stMetric"] { border-top-color: var(--primary); }
    div[data-testid="column"]:nth-of-type(4n+2) div[data-testid="stMetric"] { border-top-color: var(--ion); }
    div[data-testid="column"]:nth-of-type(4n+3) div[data-testid="stMetric"] { border-top-color: var(--amber); }
    div[data-testid="column"]:nth-of-type(4n+0) div[data-testid="stMetric"] { border-top-color: var(--coral); }

    div[data-testid="stMetricLabel"] {
        color: var(--muted) !important;
        font-size: .78rem !important;
        font-weight: 500 !important;
    }

    div[data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-size: 1.75rem !important;
        font-weight: 650 !important;
        font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
    }

    /* ---------- Section labels / cards ---------- */

    .section-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 1rem 1.1rem;
        margin: .35rem 0 1rem 0;
    }

    .section-label {
        color: #5B6784 !important;
        font-size: .72rem;
        font-weight: 500;
        margin-bottom: .4rem;
        font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
    }

    /* ---------- Telemetry terminal ---------- */

    .terminal {
        background: #04060C;
        border: 1px solid var(--border);
        border-left: 2px solid var(--emerald);
        border-radius: 4px;
        padding: .8rem 1rem;
        color: #A9B4CC;
        font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
        font-size: .77rem;
        line-height: 1.55;
        overflow-x: auto;
    }

    /* ---------- Pipeline / status cards ---------- */

    .status-card {
        background: linear-gradient(160deg, var(--card-2), var(--card));
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem;
        min-height: 95px;
        box-shadow: 0 6px 18px rgba(0,0,0,.28);
        transition: transform .18s ease, box-shadow .18s ease;
    }

    .status-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 24px rgba(0,0,0,.36);
    }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 7px;
        box-shadow: 0 0 8px currentColor;
    }

    .status-title {
        color: var(--muted);
        font-size: .78rem;
        font-weight: 500;
    }

    .status-value {
        color: var(--text);
        font-size: 1.4rem;
        font-weight: 600;
        margin-top: .3rem;
        font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
    }

    /* ---------- Badges ---------- */

    .badge-critical, .badge-warning, .badge-normal {
        display: inline-block;
        border-radius: 3px;
        padding: .2rem .45rem;
        font-size: .72rem;
        font-weight: 600;
    }

    .badge-critical {
        color: #F7C6C9;
        background: rgba(242,85,95,.14);
        border: 1px solid rgba(242,85,95,.35);
    }

    .badge-warning {
        color: #F6DBAE;
        background: rgba(242,169,59,.13);
        border: 1px solid rgba(242,169,59,.32);
    }

    .badge-normal {
        color: #AEEBD9;
        background: rgba(53,215,166,.12);
        border: 1px solid rgba(53,215,166,.3);
    }

    /* ---------- Selectboxes / BaseWeb controls ---------- */

    div[data-baseweb="select"] > div {
        background: var(--card-2) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: 8px !important;
        min-height: 42px !important;
        box-shadow: none !important;
        transition: border-color .15s ease;
    }

    div[data-baseweb="select"] input { color: var(--text) !important; }
    div[data-baseweb="select"] span { color: var(--text) !important; }
    div[data-baseweb="select"] svg { fill: #93A2C2 !important; }
    div[data-baseweb="select"] > div:hover { border-color: var(--primary) !important; }

    div[data-baseweb="popover"] {
        background: var(--card-2) !important;
        border: 1px solid var(--border) !important;
    }

    div[role="listbox"] { background: var(--card-2) !important; }

    div[role="option"] {
        background: var(--card-2) !important;
        color: var(--text) !important;
    }

    div[role="option"]:hover,
    div[role="option"][aria-selected="true"] {
        background: var(--card-hover) !important;
        color: var(--primary) !important;
    }

    /* ---------- Buttons ---------- */

    .stButton > button {
        background: var(--card-2) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: 8px !important;
        font-weight: 500;
        transition: all .15s ease;
    }

    .stButton > button:hover {
        background: var(--card-hover) !important;
        border-color: var(--primary) !important;
        color: var(--primary) !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(0,0,0,.32);
    }

    /* ---------- Dataframes ---------- */

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        background: var(--card-2) !important;
        box-shadow: 0 6px 18px rgba(0,0,0,.25);
    }

    /* ---------- Containers ---------- */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,.015);
        border-color: var(--border) !important;
        border-radius: 10px !important;
    }

    /* ---------- Dividers ---------- */

    hr {
        border-color: var(--border) !important;
        opacity: .6;
        margin: 1.1rem 0 !important;
    }

    /* ---------- Alerts ---------- */

    div[data-testid="stAlert"] {
        border-radius: 4px !important;
        border: 1px solid var(--border) !important;
        background: var(--card) !important;
    }

    /* ---------- Streamlit top chrome ---------- */

    header[data-testid="stHeader"] {
        background: rgba(6,9,17,.75) !important;
    }

    /* ---------- Scrollbars ---------- */

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--sidebar); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 8px; }
    ::-webkit-scrollbar-thumb:hover { background: #2C3B5C; }

    /* ============================================================
       ABOUT PAGE — extra components
       ============================================================ */

    .about-hero {
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.6rem 1.8rem;
        background:
            radial-gradient(700px 260px at 15% -20%, rgba(63,169,245,.16), transparent 60%),
            radial-gradient(600px 260px at 100% 0%, rgba(142,124,255,.12), transparent 60%),
            linear-gradient(160deg, var(--card-2), var(--card));
        margin-bottom: 1.3rem;
        box-shadow: 0 10px 30px rgba(0,0,0,.32);
    }

    .about-hero-flow {
        margin-top: 1rem;
        font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
        font-size: .82rem;
        color: var(--text-soft);
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: .35rem;
    }

    .flow-node {
        border: 1px solid var(--border);
        background: rgba(63,169,245,.06);
        border-radius: 6px;
        padding: .28rem .6rem;
        color: var(--text);
    }

    .flow-arrow { color: var(--muted); }

    .monitor-card {
        background: linear-gradient(160deg, var(--card-2), var(--card));
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem 1.1rem;
        min-height: 118px;
        transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    }

    .monitor-card:hover {
        transform: translateY(-3px);
        border-color: var(--primary);
        box-shadow: 0 12px 24px rgba(0,0,0,.32);
    }

    .monitor-icon { font-size: 1.25rem; }

    .monitor-title {
        color: var(--text);
        font-weight: 650;
        margin: .35rem 0 .25rem 0;
        font-size: .95rem;
    }

    .monitor-desc {
        color: var(--muted);
        font-size: .82rem;
        line-height: 1.45;
    }

    .stage-track {
        position: relative;
        margin: .3rem 0 .4rem 1.2rem;
        padding-left: 1.4rem;
        border-left: 2px solid var(--border);
    }

    .stage-item {
        position: relative;
        padding: 0 0 1.3rem 0;
    }

    .stage-item::before {
        content: "";
        position: absolute;
        left: -1.51rem;
        top: .2rem;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--bg);
        border: 2px solid var(--primary);
    }

    .stage-num {
        font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
        color: var(--primary);
        font-size: .74rem;
        font-weight: 700;
        letter-spacing: .04em;
    }

    .stage-title {
        color: var(--text);
        font-weight: 650;
        font-size: .96rem;
        margin: .1rem 0 .2rem 0;
    }

    .stage-desc {
        color: var(--muted);
        font-size: .84rem;
        line-height: 1.5;
        max-width: 72ch;
    }

    .stack-pill {
        display: inline-block;
        border: 1px solid var(--border);
        background: var(--card-2);
        color: var(--text-soft);
        border-radius: 20px;
        padding: .28rem .7rem;
        font-size: .78rem;
        margin: 0 .35rem .45rem 0;
    }

    .stack-group-label {
        color: #5B6784;
        font-size: .7rem;
        font-weight: 700;
        letter-spacing: .08em;
        margin: .8rem 0 .4rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

COLORS = {
    "bg": "#060911",
    "card": "#0E1524",
    "border": "#223050",
    "text": "#E8ECF6",
    "muted": "#6E7A96",
    "primary": "#3FA9F5",
    "ion": "#8E7CFF",
    "amber": "#F2A93B",
    "emerald": "#35D7A6",
    "coral": "#F2555F",
}


def page_header(title, kicker, subtitle):
    st.markdown(f'<div class="page-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def section_header(title, label=None):
    if label:
        st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)
    st.subheader(title)


def plotly_layout(fig, height=310):
    fig.update_layout(
        height=height,
        paper_bgcolor=COLORS["card"],
        plot_bgcolor=COLORS["card"],
        font=dict(color=COLORS["text"]),
        margin=dict(l=45, r=20, t=25, b=40),
        hovermode="x unified",
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=COLORS["muted"]),
        ),
        xaxis=dict(
            gridcolor=COLORS["border"],
            linecolor=COLORS["border"],
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor=COLORS["border"],
            linecolor=COLORS["border"],
            zeroline=False,
        ),
    )
    return fig


def _to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def line_chart(df, x, y_columns, title, colors, y_title=None):
    fig = go.Figure()
    for column, color in zip(y_columns, colors):
        fig.add_trace(
            go.Scatter(
                x=df[x],
                y=df[column],
                mode="lines+markers",
                name=column.replace("_", " ").title(),
                line=dict(color=color, width=2.5),
                marker=dict(size=5, color=color, line=dict(width=1, color=COLORS["bg"])),
                fill="tozeroy",
                fillcolor=_to_rgba(color, 0.12),
            )
        )
    fig.update_layout(title=title, yaxis_title=y_title)
    return plotly_layout(fig)


def show_kpis(items):
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        label = item[1]
        value = item[2]
        with col:
            st.metric(label, value)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">🛰️</div>
            <div class="brand-text">
                <div class="brand-name">Orbitalis</div>
                <div class="brand-sub">Space Data Systems</div>
            </div>
        </div>
        <div class="system-status"><span class="live-dot"></span> All systems operational</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="nav-label">NAVIGATION</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigate",
        [
            "🛰️ Mission Overview",
            "📡 Satellite Detail",
            "📈 Telemetry Trends",
            "⚠️ Anomaly Center",
            "🔧 Pipeline Health",
            "ℹ️ About",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("Mission Control")
    st.caption("Telemetry intelligence platform")
    st.caption("Built on AWS Athena, S3 and Iceberg")


# ============================================================
# 1. MISSION OVERVIEW
# ============================================================

if page == "🛰️ Mission Overview":
    page_header(
        "Mission Overview",
        "Fleet dashboard, build 2.4",
        "Orbitalis satellite fleet — live analytics from AWS Athena",
    )

    telemetry_df = run_query(
        """
        SELECT
            COUNT(*) AS total_events,
            COUNT(DISTINCT satellite_id) AS total_satellites
        FROM silver_telemetry
        """
    )

    anomaly_df = run_query(
        """
        SELECT
            COUNT(*) AS total_anomalies,
            SUM(
                CASE
                    WHEN severity = 'CRITICAL' THEN 1
                    ELSE 0
                END
            ) AS critical_anomalies
        FROM satellite_anomalies
        """
    )

    total_events = int(telemetry_df.iloc[0]["total_events"])
    total_satellites = int(telemetry_df.iloc[0]["total_satellites"])
    total_anomalies = int(anomaly_df.iloc[0]["total_anomalies"])
    critical_anomalies = int(anomaly_df.iloc[0]["critical_anomalies"] or 0)

    show_kpis(
        [
            (None, "📡 Total Events", f"{total_events:,}"),
            (None, "🛰️ Satellites", f"{total_satellites:,}"),
            (None, "⚠️ Total Anomalies", f"{total_anomalies:,}"),
            (None, "🔴 Critical Anomalies", f"{critical_anomalies:,}"),
        ]
    )

    st.divider()

    section_header("Fleet Health Summary", "Fleet telemetry")

    health_df = run_query(
        """
        SELECT
            satellite_id,
            event_date,
            avg_battery_voltage,
            max_temperature,
            avg_signal_strength,
            event_count
        FROM satellite_health_daily
        ORDER BY event_date DESC, satellite_id
        """
    )

    with st.container(border=True):
        st.dataframe(
            health_df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 2. SATELLITE DETAIL
# ============================================================

elif page == "📡 Satellite Detail":
    page_header(
        "Satellite Detail",
        "Per-satellite telemetry",
        "Detailed telemetry and recent operational state for an individual satellite",
    )

    satellites_df = run_query(
        """
        SELECT DISTINCT satellite_id
        FROM silver_telemetry
        ORDER BY satellite_id
        """
    )

    satellite_list = satellites_df["satellite_id"].tolist()

    if not satellite_list:
        st.warning("No satellites are currently available in silver_telemetry.")
        st.stop()

    selected_satellite = st.selectbox(
        "Select Satellite",
        satellite_list,
    )

    summary_df = run_query(
        f"""
        SELECT
            COUNT(*) AS event_count,
            AVG(battery_voltage) AS avg_battery,
            MAX(battery_temperature) AS max_temperature,
            AVG(signal_strength) AS avg_signal
        FROM silver_telemetry
        WHERE satellite_id = '{selected_satellite}'
        """
    )

    event_count = int(summary_df.iloc[0]["event_count"])
    avg_battery = float(summary_df.iloc[0]["avg_battery"])
    max_temperature = float(summary_df.iloc[0]["max_temperature"])
    avg_signal = float(summary_df.iloc[0]["avg_signal"])

    show_kpis(
        [
            (None, "📡 Events", f"{event_count:,}"),
            (None, "🔋 Avg Battery", f"{avg_battery:.2f} V"),
            (None, "🌡️ Max Temperature", f"{max_temperature:.2f} °C"),
            (None, "📶 Avg Signal", f"{avg_signal:.2f}"),
        ]
    )

    st.divider()

    section_header(
        f"Recent Telemetry — {selected_satellite}",
        "Live telemetry log",
    )

    telemetry_df = run_query(
        f"""
        SELECT
            event_id,
            event_timestamp,
            latitude,
            longitude,
            altitude_km,
            velocity_kmh,
            battery_voltage,
            battery_temperature,
            fuel_level,
            radiation_level,
            signal_strength,
            communication_status
        FROM silver_telemetry
        WHERE satellite_id = '{selected_satellite}'
        ORDER BY event_timestamp DESC
        LIMIT 20
        """
    )

    with st.container(border=True):
        st.markdown(
            '<div class="terminal">[TELEMETRY STREAM] '
            f'{selected_satellite}  |  LAST 20 EVENTS  |  ATHENA / SILVER</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            telemetry_df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 3. TELEMETRY TRENDS
# ============================================================

elif page == "📈 Telemetry Trends":
    page_header(
        "Telemetry Trends",
        "Flight-health time series",
        "Satellite health and orbital trends from AWS Athena",
    )

    satellites_df = run_query(
        """
        SELECT DISTINCT satellite_id
        FROM silver_telemetry
        ORDER BY satellite_id
        """
    )

    satellite_list = satellites_df["satellite_id"].tolist()

    if not satellite_list:
        st.warning("No satellites are currently available in silver_telemetry.")
        st.stop()

    selected_satellite = st.selectbox(
        "Select Satellite",
        satellite_list,
        key="trend_satellite",
    )

    health_df = run_query(
        f"""
        SELECT
            event_date,
            avg_battery_voltage,
            max_temperature,
            avg_signal_strength
        FROM satellite_health_daily
        WHERE satellite_id = '{selected_satellite}'
        ORDER BY event_date
        """
    )

    health_df["event_date"] = pd.to_datetime(health_df["event_date"])

    section_header(
        f"Health Trends — {selected_satellite}",
        "Power, thermal and comms",
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔋 Battery Voltage")
        battery_chart = line_chart(
            health_df,
            "event_date",
            ["avg_battery_voltage"],
            "Average Battery Voltage",
            [COLORS["amber"]],
            "Voltage (V)",
        )
        st.plotly_chart(
            battery_chart,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with col2:
        st.markdown("#### 🌡️ Temperature")
        temperature_chart = line_chart(
            health_df,
            "event_date",
            ["max_temperature"],
            "Maximum Battery Temperature",
            [COLORS["coral"]],
            "Temperature (°C)",
        )
        st.plotly_chart(
            temperature_chart,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    st.divider()

    orbit_df = run_query(
        f"""
        SELECT
            event_date,
            avg_altitude,
            min_altitude,
            max_altitude,
            avg_velocity
        FROM satellite_orbit_summary
        WHERE satellite_id = '{selected_satellite}'
        ORDER BY event_date
        """
    )

    orbit_df["event_date"] = pd.to_datetime(orbit_df["event_date"])

    section_header(
        f"Orbital Trends — {selected_satellite}",
        "Orbit and flight dynamics",
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🛰️ Altitude")
        altitude_chart = line_chart(
            orbit_df,
            "event_date",
            ["avg_altitude", "min_altitude", "max_altitude"],
            "Orbital Altitude Envelope",
            [COLORS["primary"], COLORS["muted"], COLORS["emerald"]],
            "Altitude (km)",
        )
        st.plotly_chart(
            altitude_chart,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with col2:
        st.markdown("#### 🚀 Velocity")
        velocity_chart = line_chart(
            orbit_df,
            "event_date",
            ["avg_velocity"],
            "Average Orbital Velocity",
            [COLORS["emerald"]],
            "Velocity (km/h)",
        )
        st.plotly_chart(
            velocity_chart,
            use_container_width=True,
            config={"displayModeBar": False},
        )


# ============================================================
# 4. ANOMALY CENTER
# ============================================================

elif page == "⚠️ Anomaly Center":
    page_header(
        "Anomaly Center",
        "Flight-safety exceptions",
        "Satellite anomalies detected by the Orbitalis anomaly engine",
    )

    anomaly_df = run_query(
        """
        SELECT
            satellite_id,
            event_timestamp,
            battery_voltage,
            battery_temperature,
            fuel_level,
            anomaly_type,
            severity
        FROM satellite_anomalies
        ORDER BY event_timestamp DESC
        """
    )

    anomaly_df["battery_voltage"] = pd.to_numeric(
        anomaly_df["battery_voltage"],
        errors="coerce",
    )

    anomaly_df["battery_temperature"] = pd.to_numeric(
        anomaly_df["battery_temperature"],
        errors="coerce",
    )

    anomaly_df["fuel_level"] = pd.to_numeric(
        anomaly_df["fuel_level"],
        errors="coerce",
    )

    total_anomalies = len(anomaly_df)

    critical_count = len(
        anomaly_df[
            anomaly_df["severity"].str.upper() == "CRITICAL"
        ]
    )

    warning_count = len(
        anomaly_df[
            anomaly_df["severity"].str.upper() == "WARNING"
        ]
    )

    show_kpis(
        [
            (None, "⚠️ Total Anomalies", f"{total_anomalies:,}"),
            (None, "🔴 Critical", f"{critical_count:,}"),
            (None, "🟡 Warning", f"{warning_count:,}"),
        ]
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        satellite_options = ["All"] + sorted(
            anomaly_df["satellite_id"].dropna().unique().tolist()
        )

        selected_satellite = st.selectbox(
            "Filter by Satellite",
            satellite_options,
            key="anomaly_satellite",
        )

    with col2:
        severity_options = ["All"] + sorted(
            anomaly_df["severity"].dropna().unique().tolist()
        )

        selected_severity = st.selectbox(
            "Filter by Severity",
            severity_options,
            key="anomaly_severity",
        )

    filtered_df = anomaly_df.copy()

    if selected_satellite != "All":
        filtered_df = filtered_df[
            filtered_df["satellite_id"] == selected_satellite
        ]

    if selected_severity != "All":
        filtered_df = filtered_df[
            filtered_df["severity"] == selected_severity
        ]

    section_header("Detected Anomalies", "Exception queue")

    # Keep the original data columns, while applying enterprise styling.
    display_df = filtered_df.copy()

    if "severity" in display_df.columns:
        display_df["severity"] = display_df["severity"].astype(str).str.upper()

    def severity_style(value):
        value = str(value).upper()
        if value == "CRITICAL":
            return "background-color: rgba(242,85,95,.18); color: #FBD0D3; font-weight: 700;"
        if value == "WARNING":
            return "background-color: rgba(242,169,59,.15); color: #F9E3BC; font-weight: 700;"
        return "background-color: rgba(53,215,166,.12); color: #BFF2E2; font-weight: 700;"

    styled_df = display_df.style.applymap(
        severity_style,
        subset=["severity"],
    )

    with st.container(border=True):
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 5. PIPELINE HEALTH
# ============================================================

elif page == "🔧 Pipeline Health":
    page_header(
        "Pipeline Health",
        "Ingest pipeline status",
        "Data engineering pipeline health from S3 and AWS Athena",
    )

    # ---------------------------------------------------------
    # 1. Valid / processed records from Silver Iceberg table
    # ---------------------------------------------------------

    valid_df = run_query(
        """
        SELECT COUNT(*) AS valid_records
        FROM silver_telemetry
        """
    )

    valid_records = int(valid_df.iloc[0]["valid_records"])

    # ---------------------------------------------------------
    # 2. Count S3 objects in pipeline folders
    # ---------------------------------------------------------

    s3_client = boto3.client(
        "s3",
        region_name="ap-south-1",
    )

    BUCKET = "orbitalis-data-jatin2026"

    def count_s3_objects(prefix):
        count = 0
        continuation_token = None

        while True:
            params = {
                "Bucket": BUCKET,
                "Prefix": prefix,
            }

            if continuation_token:
                params["ContinuationToken"] = continuation_token

            response = s3_client.list_objects_v2(**params)

            for obj in response.get("Contents", []):
                # Ignore Hadoop/S3 directory marker objects
                if not obj["Key"].endswith("/"):
                    count += 1

            if not response.get("IsTruncated"):
                break

            continuation_token = response.get("NextContinuationToken")

        return count

    rejected_files = count_s3_objects("rejected/telemetry/")
    late_files = count_s3_objects("late/telemetry/")
    duplicate_files = count_s3_objects("duplicates/telemetry/")

    # ---------------------------------------------------------
    # 3. Pipeline KPI cards
    # ---------------------------------------------------------

    show_kpis(
        [
            (None, "✅ Valid / Processed", f"{valid_records:,}"),
            (None, "❌ Rejected Files", f"{rejected_files:,}"),
            (None, "⏰ Late Files", f"{late_files:,}"),
            (None, "♻️ Duplicate Files", f"{duplicate_files:,}"),
        ]
    )

    st.divider()

    section_header("Pipeline Stage Status", "Pipeline control")

    stage_cols = st.columns(4)

    stages = [
        ("Processed", valid_records, COLORS["emerald"]),
        ("Rejected", rejected_files, COLORS["coral"]),
        ("Late", late_files, COLORS["amber"]),
        ("Duplicates", duplicate_files, COLORS["muted"]),
    ]

    for col, (name, count, color) in zip(stage_cols, stages):
        with col:
            st.markdown(
                f"""
                <div class="status-card">
                    <div class="status-title">
                        <span class="status-dot" style="background:{color};"></span>
                        {name}
                    </div>
                    <div class="status-value">{count:,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # ---------------------------------------------------------
    # 4. Pipeline storage summary
    # ---------------------------------------------------------

    section_header("Pipeline Storage Summary", "Storage inventory")

    pipeline_df = pd.DataFrame(
        {
            "Pipeline Stage": [
                "Valid / Processed",
                "Rejected",
                "Late",
                "Duplicates",
            ],
            "Count": [
                valid_records,
                rejected_files,
                late_files,
                duplicate_files,
            ],
            "Source": [
                "Athena → silver_telemetry",
                "S3 → rejected/telemetry/",
                "S3 → late/telemetry/",
                "S3 → duplicates/telemetry/",
            ],
        }
    )

    with st.container(border=True):
        st.dataframe(
            pipeline_df,
            use_container_width=True,
            hide_index=True,
        )

    st.info(
        "Valid / Processed is an actual record count from the Silver "
        "Iceberg table. Rejected, Late, and Duplicate values are "
        "currently S3 object/file counts."
    )


# ============================================================
# 6. ABOUT — UI only, no backend calls, no Athena/S3 traffic
# ============================================================

elif page == "ℹ️ About":
    page_header(
        "About Orbitalis",
        "Platform overview",
        "An end-to-end satellite telemetry data engineering platform, "
        "from real-time ingestion to Mission Control analytics",
    )

    # ---------------- Hero: one-line lifecycle ----------------

    hero_nodes = [
        "Simulator", "Kinesis", "S3 Bronze", "PySpark",
        "Iceberg Silver", "Gold Tables", "Athena", "Mission Control",
    ]
    hero_html = "".join(
        f'<span class="flow-node">{node}</span>'
        + ('<span class="flow-arrow">→</span>' if i < len(hero_nodes) - 1 else "")
        for i, node in enumerate(hero_nodes)
    )

    st.markdown(
        f"""
        <div class="about-hero">
            <div class="page-kicker" style="margin-bottom:.4rem;">Lifecycle</div>
            <div style="color:var(--text); font-size:1.05rem; font-weight:650; max-width:70ch;">
                Orbitalis ingests, validates, processes, stores and monitors
                satellite telemetry in near real time, then surfaces it here
                as operational analytics.
            </div>
            <div class="about-hero-flow">{hero_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------- What Orbitalis monitors ----------------

    section_header("What Orbitalis Monitors", "Coverage")

    monitors = [
        ("🛰️", "Satellite Health", "Battery voltage, temperature, signal strength and other operational metrics."),
        ("📡", "Telemetry", "Ingestion and historical analysis of real-time-style telemetry events."),
        ("⚠️", "Anomalies", "Detection and triage of abnormal satellite conditions by severity."),
        ("🌍", "Orbit Analytics", "Altitude, velocity and positional telemetry over time."),
        ("🔧", "Pipeline Health", "Validation, rejection, late-event and processing metrics."),
        ("☁️", "Cloud Infrastructure", "Streaming, storage, processing and analytics on AWS."),
    ]

    m_cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(monitors):
        with m_cols[i % 3]:
            st.markdown(
                f"""
                <div class="monitor-card">
                    <div class="monitor-icon">{icon}</div>
                    <div class="monitor-title">{title}</div>
                    <div class="monitor-desc">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if i % 3 == 2 and i != len(monitors) - 1:
            st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

    st.divider()



    # ---------------- Architecture layers ----------------

    section_header("Architecture Layers", "Layer reference")

    layers_df = pd.DataFrame(
        {
            "Layer": [
                "Source", "Streaming", "Bronze", "Processing", "Silver",
                "Gold", "Catalog", "Query", "Dashboard", "Monitoring",
                "Security", "IaC", "CI/CD",
            ],
            "Technology": [
                "Python Simulator", "Amazon Kinesis", "Amazon S3",
                "Apache Spark / PySpark", "Apache Iceberg", "Iceberg Tables",
                "AWS Glue", "Amazon Athena", "Streamlit + Plotly",
                "CloudWatch + SNS", "IAM + KMS", "Terraform", "GitHub Actions",
            ],
            "Purpose": [
                "Generate telemetry", "Real-time ingestion", "Raw telemetry storage",
                "Validation & transformation", "Validated telemetry",
                "Analytics-ready datasets", "Table metadata / catalog",
                "SQL analytics", "Mission visualization", "Pipeline observability",
                "Access & encryption", "Infrastructure management",
                "Automated testing",
            ],
        }
    )

    with st.container(border=True):
        st.dataframe(layers_df, use_container_width=True, hide_index=True)

    st.divider()

    # ---------------- Technology stack ----------------

    section_header("Technology Stack", "Stack reference")

    stack_groups = {
        "PYTHON": ["Telemetry Simulator", "Data Processing Utilities"],
        "AWS": ["Kinesis Data Streams", "S3", "Glue", "Athena", "CloudWatch", "SNS", "IAM / KMS"],
        "DATA ENGINEERING": ["Apache Spark", "PySpark", "Apache Iceberg"],
        "ANALYTICS": ["Streamlit", "Pandas", "Plotly"],
        "ENGINEERING": ["Terraform", "Git", "GitHub Actions"],
    }

    for group, items in stack_groups.items():
        st.markdown(f'<div class="stack-group-label">{group}</div>', unsafe_allow_html=True)
        pills = "".join(f'<span class="stack-pill">{item}</span>' for item in items)
        st.markdown(pills, unsafe_allow_html=True)

    st.divider()

    st.info(
        "Orbitalis is a demonstration platform showing how high-volume "
        "satellite telemetry can be ingested, validated, processed, stored "
        "and analyzed with modern cloud data engineering tools — end to "
        "end, from simulator to Mission Control."
    )
"""
Orbitalis Mission Control Dashboard — Production UI
Space Tech / Aerospace Enterprise Mission Control interface.

Backend logic intentionally preserved:
- AWS Athena via `run_query`
- AWS S3 object counts via boto3
- Existing Athena table names and SQL query semantics
- Existing five dashboard pages
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
# ENTERPRISE MISSION-CONTROL THEME
# ============================================================

st.markdown(
    """
    <style>
    /* ============================================================
       ORBITALIS MISSION CONTROL — DARK ENTERPRISE THEME
       ============================================================ */

    :root {
        --bg: #0B1220;
        --bg-2: #0E1728;
        --sidebar: #080E1A;
        --card: #151F32;
        --card-2: #111A2B;
        --card-hover: #19263D;
        --border: #2A3A52;
        --border-soft: #203047;

        --text: #F8FAFC;
        --text-soft: #CBD5E1;
        --muted: #94A3B8;

        --primary: #38BDF8;
        --primary-soft: rgba(56,189,248,.10);
        --emerald: #10B981;
        --amber: #F59E0B;
        --coral: #EF4444;
        --violet: #A78BFA;
    }

    /* ---------- App shell ---------- */

    .stApp {
        background:
            radial-gradient(circle at 85% 5%, rgba(56,189,248,.055), transparent 28%),
            linear-gradient(135deg, var(--bg), var(--bg-2));
        color: var(--text);
    }

    .main .block-container {
        max-width: 1600px;
        padding-top: 2.2rem;
        padding-bottom: 3.5rem;
    }

    /* ---------- Typography ---------- */

    h1, h2, h3, h4, h5, h6 {
        color: var(--text) !important;
        letter-spacing: -0.025em;
    }

    h1 {
        font-size: 2.15rem !important;
        font-weight: 800 !important;
        line-height: 1.1 !important;
    }

    h2 {
        font-weight: 750 !important;
    }

    h3, h4 {
        font-weight: 700 !important;
    }

    p, label, .stCaption {
        color: var(--muted);
    }

    /* ---------- Sidebar ---------- */

    section[data-testid="stSidebar"] {
        background: var(--sidebar) !important;
        border-right: 1px solid #26364D !important;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.15rem;
    }

    section[data-testid="stSidebar"] .stMarkdown {
        color: var(--text-soft);
    }

    .brand {
        padding: .45rem .35rem 1.25rem .35rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.15rem;
    }

    .brand-name {
        font-size: 1.15rem;
        font-weight: 850;
        letter-spacing: .13em;
        color: var(--text) !important;
    }

    .brand-sub {
        color: #64748B !important;
        font-size: .68rem;
        letter-spacing: .10em;
        margin-top: .25rem;
    }

    .system-status {
        display: inline-flex;
        align-items: center;
        gap: .4rem;
        margin-top: .8rem;
        padding: .38rem .65rem;
        border: 1px solid rgba(16,185,129,.45);
        border-radius: 999px;
        background: rgba(16,185,129,.10);
        color: #6EE7B7 !important;
        font-size: .69rem;
        font-weight: 800;
        letter-spacing: .05em;
        box-shadow: 0 0 18px rgba(16,185,129,.06);
    }

    div[data-testid="stRadio"] label {
        color: #CBD5E1 !important;
        font-weight: 600;
        transition: all .15s ease;
    }

    div[data-testid="stRadio"] label:hover {
        color: var(--primary) !important;
    }

    div[data-testid="stRadio"] [role="radiogroup"] {
        gap: .2rem;
    }

    /* ---------- Page header ---------- */

    .page-kicker {
        display: inline-block;
        padding: .38rem .68rem;
        margin-bottom: .72rem;
        border: 1px solid rgba(56,189,248,.28);
        border-radius: 7px;
        background: var(--primary-soft);
        color: var(--primary) !important;
        font-size: .67rem;
        font-weight: 850;
        letter-spacing: .13em;
        text-transform: uppercase;
    }

    .page-subtitle {
        color: var(--muted) !important;
        margin-top: -.5rem;
        margin-bottom: 1.45rem;
        font-size: .92rem;
    }

    /* ---------- KPI cards ---------- */

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #17243A, #111A2B) !important;
        border: 1px solid #2F415B !important;
        border-radius: 12px !important;
        padding: 1rem 1.1rem !important;
        min-height: 112px !important;
        box-shadow:
            0 8px 25px rgba(0,0,0,.22),
            inset 0 1px 0 rgba(255,255,255,.025);
        transition: all .18s ease;
    }

    div[data-testid="stMetric"]:hover {
        border-color: rgba(56,189,248,.65) !important;
        transform: translateY(-1px);
        box-shadow:
            0 10px 30px rgba(0,0,0,.28),
            0 0 20px rgba(56,189,248,.07);
    }

    div[data-testid="stMetricLabel"] {
        color: var(--muted) !important;
        font-size: .72rem !important;
        font-weight: 750 !important;
        letter-spacing: .055em;
    }

    div[data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-size: 1.82rem !important;
        font-weight: 800 !important;
    }

    /* ---------- Section labels / cards ---------- */

    .section-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 11px;
        padding: 1rem 1.1rem;
        margin: .35rem 0 1rem 0;
    }

    .section-label {
        color: #64748B !important;
        font-size: .66rem;
        font-weight: 850;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-bottom: .55rem;
    }

    /* ---------- Telemetry terminal ---------- */

    .terminal {
        background: #080F1D;
        border: 1px solid #26364D;
        border-radius: 9px;
        padding: .9rem 1rem;
        color: #CBD5E1;
        font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
        font-size: .77rem;
        line-height: 1.55;
        overflow-x: auto;
        box-shadow: inset 0 0 25px rgba(0,0,0,.18);
    }

    /* ---------- Pipeline status cards ---------- */

    .status-card {
        background: linear-gradient(145deg, #17243A, #111A2B);
        border: 1px solid var(--border);
        border-radius: 11px;
        padding: 1rem;
        min-height: 105px;
        box-shadow: 0 7px 22px rgba(0,0,0,.16);
    }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 7px;
        box-shadow: 0 0 9px currentColor;
    }

    .status-title {
        color: var(--muted);
        font-size: .70rem;
        font-weight: 800;
        letter-spacing: .08em;
        text-transform: uppercase;
    }

    .status-value {
        color: var(--text);
        font-size: 1.48rem;
        font-weight: 800;
        margin-top: .3rem;
    }

    /* ---------- Badges ---------- */

    .badge-critical,
    .badge-warning,
    .badge-normal {
        display: inline-block;
        border-radius: 5px;
        padding: .22rem .48rem;
        font-size: .68rem;
        font-weight: 800;
        letter-spacing: .05em;
    }

    .badge-critical {
        color: #FECACA;
        background: rgba(239,68,68,.15);
        border: 1px solid rgba(239,68,68,.4);
    }

    .badge-warning {
        color: #FDE68A;
        background: rgba(245,158,11,.13);
        border: 1px solid rgba(245,158,11,.38);
    }

    .badge-normal {
        color: #A7F3D0;
        background: rgba(16,185,129,.12);
        border: 1px solid rgba(16,185,129,.35);
    }

    /* ---------- Selectboxes / BaseWeb controls ---------- */

    div[data-baseweb="select"] > div {
        background: #162033 !important;
        border: 1px solid #3B4B63 !important;
        color: var(--text) !important;
        border-radius: 8px !important;
        min-height: 44px !important;
        box-shadow: none !important;
    }

    div[data-baseweb="select"] input {
        color: var(--text) !important;
    }

    div[data-baseweb="select"] span {
        color: var(--text) !important;
    }

    div[data-baseweb="select"] svg {
        fill: #94A3B8 !important;
    }

    div[data-baseweb="select"] > div:hover {
        border-color: var(--primary) !important;
    }

    div[data-baseweb="popover"] {
        background: #162033 !important;
        border: 1px solid #3B4B63 !important;
    }

    div[role="listbox"] {
        background: #162033 !important;
    }

    div[role="option"] {
        background: #162033 !important;
        color: var(--text) !important;
    }

    div[role="option"]:hover,
    div[role="option"][aria-selected="true"] {
        background: #24344D !important;
        color: var(--primary) !important;
    }

    /* ---------- Buttons ---------- */

    .stButton > button {
        background: #162033 !important;
        border: 1px solid #3B4B63 !important;
        color: var(--text) !important;
        border-radius: 8px !important;
        font-weight: 650;
    }

    .stButton > button:hover {
        background: #1B2A42 !important;
        border-color: var(--primary) !important;
        color: var(--primary) !important;
    }

    /* ---------- Dataframes ---------- */

    div[data-testid="stDataFrame"] {
        border: 1px solid #2A3A52 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        background: #111A2B !important;
        box-shadow: 0 8px 24px rgba(0,0,0,.16);
    }

    /* ---------- Containers ---------- */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(17,26,43,.42);
        border-color: var(--border) !important;
        border-radius: 11px !important;
    }

    /* ---------- Dividers ---------- */

    hr {
        border-color: var(--border) !important;
        opacity: .65;
        margin: 1.1rem 0 !important;
    }

    /* ---------- Alerts ---------- */

    div[data-testid="stAlert"] {
        border-radius: 9px !important;
        border: 1px solid var(--border) !important;
        background: var(--card) !important;
    }

    /* ---------- Streamlit top chrome ---------- */

    header[data-testid="stHeader"] {
        background: rgba(11,18,32,.72) !important;
    }

    /* ---------- Scrollbars ---------- */

    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #080E1A;
    }

    ::-webkit-scrollbar-thumb {
        background: #2A3A52;
        border-radius: 8px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #3B4B63;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

COLORS = {
    "bg": "#0B1220",
    "card": "#151F32",
    "border": "#2A3A52",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
    "primary": "#38BDF8",
    "amber": "#F59E0B",
    "emerald": "#10B981",
    "coral": "#EF4444",
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


def line_chart(df, x, y_columns, title, colors, y_title=None):
    fig = go.Figure()
    for column, color in zip(y_columns, colors):
        fig.add_trace(
            go.Scatter(
                x=df[x],
                y=df[column],
                mode="lines+markers",
                name=column.replace("_", " ").title(),
                line=dict(color=color, width=2),
                marker=dict(size=4, color=color),
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
            <div class="brand-name">ORBITALIS</div>
            <div class="brand-sub">// SPACE DATA SYSTEMS</div>
            <div class="system-status">● SYSTEMS OPERATIONAL</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**MISSION NAVIGATION**")
    page = st.radio(
        "Navigate",
        [
            "🛰️ Mission Overview",
            "📡 Satellite Detail",
            "📈 Telemetry Trends",
            "⚠️ Anomaly Center",
            "🔧 Pipeline Health",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("MISSION CONTROL")
    st.caption("Telemetry Intelligence Platform")
    st.caption("AWS Athena  •  S3  •  Iceberg")


# ============================================================
# 1. MISSION OVERVIEW
# ============================================================

if page == "🛰️ Mission Overview":
    page_header(
        "Mission Overview",
        "MISSION CONTROL ARCHITECTURE v2.4",
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

    section_header("Fleet Health Summary", "FLEET TELEMETRY")

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
        "ASSET TELEMETRY // DEEP DIVE",
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
        "LIVE TELEMETRY LOG",
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
        "TIME-SERIES ANALYTICS // FLIGHT HEALTH",
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
        "POWER / THERMAL / COMMUNICATION",
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
        "ORBIT / FLIGHT DYNAMICS",
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🛰️ Altitude")
        altitude_chart = line_chart(
            orbit_df,
            "event_date",
            ["avg_altitude", "min_altitude", "max_altitude"],
            "Orbital Altitude Envelope",
            [COLORS["amber"], COLORS["muted"], COLORS["emerald"]],
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
        "FLIGHT SAFETY // EXCEPTION MANAGEMENT",
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

    section_header("Detected Anomalies", "EXCEPTION QUEUE")

    # Keep the original data columns, while applying enterprise styling.
    display_df = filtered_df.copy()

    if "severity" in display_df.columns:
        display_df["severity"] = display_df["severity"].astype(str).str.upper()

    def severity_style(value):
        value = str(value).upper()
        if value == "CRITICAL":
            return "background-color: rgba(239,68,68,.18); color: #FECACA; font-weight: 700;"
        if value == "WARNING":
            return "background-color: rgba(245,158,11,.15); color: #FDE68A; font-weight: 700;"
        return "background-color: rgba(16,185,129,.12); color: #A7F3D0; font-weight: 700;"

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
        "DATA ENGINEERING // PIPELINE OBSERVABILITY",
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

    section_header("Pipeline Stage Status", "PIPELINE CONTROL")

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

    section_header("Pipeline Storage Summary", "STORAGE INVENTORY")

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

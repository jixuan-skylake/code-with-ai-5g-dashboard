"""5G Signal Visualization Dashboard - basic-level (basic-done) entrypoint.

This file fulfills the contest's basic-level requirements:

1. ``pandas`` loads ``data/signal_samples.csv``.
2. ``pydeck`` renders an interactive 2D map; points are colored by
   ``RSRP_dBm`` ( > -90 green, < -110 red, mid yellow/orange).
3. A data-overview chart below the map shows per-band cell counts and
   supports switching between a bar chart and a pie chart.

The advanced-level commit (``advanced-done``) layers on sidebar filters,
3D pillar maps, KPI cards, animated CSS, and pytest coverage.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

from src.coloring import attach_color_columns
from src.data_loader import load_signal_samples


# ----------------------------- Page config -----------------------------
st.set_page_config(
    page_title="5G 信号态势看板",
    page_icon="📡",
    layout="wide",
)

# A minimal dark-mode polish so the basic build doesn't look default-grey.
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; }
      h1, h2, h3 { color: #e5f6ff; }
      div[data-testid="stMetricValue"] { color: #2ecc71; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------ Data load ------------------------------
DATA_PATH = Path(__file__).resolve().parent / "data" / "signal_samples.csv"


@st.cache_data(show_spinner=False)
def _load() -> pd.DataFrame:
    """Cached wrapper so Streamlit reruns don't re-parse the CSV."""
    return load_signal_samples(DATA_PATH)


df = _load()
df_colored = attach_color_columns(df)


# --------------------------------- UI ----------------------------------
st.title("📡 5G 信号态势看板")
st.caption(
    "Code with AI 海选赛 · 基础关卡演示 · 数据来源：besa-2026/code-with-ai-contest"
)

# Quick KPI strip so the first screen feels like a real dashboard.
col1, col2, col3 = st.columns(3)
col1.metric("采样点", f"{len(df):,}")
col2.metric("覆盖小区", f"{df['CellID'].nunique():,}")
col3.metric("平均 RSRP (dBm)", f"{df['RSRP_dBm'].mean():.1f}")


# 2D interactive map: ScatterplotLayer with per-row RGBA from src.coloring.
st.subheader("🗺️ 信号点地图（颜色按 RSRP_dBm 分级）")

view_state = pdk.ViewState(
    latitude=float(df["Latitude"].mean()),
    longitude=float(df["Longitude"].mean()),
    zoom=11,
    pitch=0,
)

scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_colored,
    get_position="[Longitude, Latitude]",
    get_fill_color="color",
    get_radius=80,
    pickable=True,
    opacity=0.85,
    radius_min_pixels=3,
    radius_max_pixels=20,
)

st.pydeck_chart(
    pdk.Deck(
        layers=[scatter_layer],
        initial_view_state=view_state,
        map_style="dark",
        tooltip={
            "html": (
                "<b>CellID</b>: {CellID}<br/>"
                "<b>Band</b>: {Band}<br/>"
                "<b>RSRP</b>: {RSRP_dBm} dBm<br/>"
                "<b>SINR</b>: {SINR_dB} dB<br/>"
                "<b>Download</b>: {Download_Mbps} Mbps"
            ),
            "style": {"backgroundColor": "#0f1c2e", "color": "#fff"},
        },
    )
)

# Color-tier legend so the spec mapping is unambiguous to the reviewer.
st.markdown(
    """
    <div style='display:flex; gap:1.4rem; font-size:0.9rem; margin: 0.4rem 0 1.4rem;'>
      <span><span style='display:inline-block;width:12px;height:12px;background:#2ecc71;
        border-radius:50%;margin-right:6px;'></span>RSRP &gt; -90 dBm（优）</span>
      <span><span style='display:inline-block;width:12px;height:12px;background:#f1c40f;
        border-radius:50%;margin-right:6px;'></span>-100 ~ -90 dBm（良）</span>
      <span><span style='display:inline-block;width:12px;height:12px;background:#e67e22;
        border-radius:50%;margin-right:6px;'></span>-110 ~ -100 dBm（中）</span>
      <span><span style='display:inline-block;width:12px;height:12px;background:#e74c3c;
        border-radius:50%;margin-right:6px;'></span>RSRP &lt; -110 dBm（弱）</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# ----------------------------- Overview chart --------------------------
st.subheader("📊 数据概览：各频段基站数量")

chart_kind = st.radio(
    "图表类型",
    options=("柱状图", "饼图"),
    horizontal=True,
    index=0,
)

band_counts = (
    df.groupby("Band")["CellID"]
    .nunique()
    .reset_index(name="基站数量")
    .sort_values("基站数量", ascending=False)
)

if chart_kind == "柱状图":
    fig = px.bar(
        band_counts,
        x="Band",
        y="基站数量",
        text="基站数量",
        color="Band",
        template="plotly_dark",
    )
    fig.update_traces(textposition="outside")
else:
    fig = px.pie(
        band_counts,
        names="Band",
        values="基站数量",
        hole=0.4,
        template="plotly_dark",
    )

st.plotly_chart(fig, use_container_width=True)

with st.expander("查看原始数据 (前 50 行)"):
    st.dataframe(df.head(50), use_container_width=True)

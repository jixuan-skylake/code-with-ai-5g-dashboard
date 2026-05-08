"""5G Signal Visualization Dashboard - advanced-level (advanced-done).

What this build adds on top of ``basic-done``:

* Left sidebar with three live filters (band multi-select, RSRP range
  slider, terminal-type multi-select) plus a download-speed range slider.
* Tabbed map view with two pydeck layers driven by the same filtered
  dataframe: a 2D ScatterplotLayer and a 3D ColumnLayer whose pillar
  heights are normalized from ``Download_Mbps`` (via ``src.heights``).
* A "war-room"-style dark theme with KPI tiles, gradient cards, a pulsing
  online indicator, and a fade-in title; CSS lives entirely in ``st.markdown``
  so the dashboard remains a single-file launch.
* Multiple overview charts (band cell counts, terminal mix, RSRP
  distribution) under the map.

The data ingestion, color tiering, filter math, and 3D height scaling all
delegate to pure functions in ``src/``; this module is the orchestration
+ presentation layer only.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

from src.coloring import (
    COLOR_EXCELLENT,
    COLOR_FAIR,
    COLOR_GOOD,
    COLOR_POOR,
    attach_color_columns,
)
from src.data_loader import detect_speed_column, load_signal_samples
from src.filters import apply_filters
from src.heights import normalize_height


# =====================================================================
# Page / theme
# =====================================================================
st.set_page_config(
    page_title="5G 信号态势作战室",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Inline CSS: a deliberately compact "war room" treatment. We avoid a
# pure blue/purple palette by mixing in the green/red signal semantics
# called out in the spec, and a graphite background so map colors pop.
st.markdown(
    """
    <style>
      :root {
        --accent-green: #2ecc71;
        --accent-amber: #f1c40f;
        --accent-red:   #e74c3c;
        --panel-bg:     rgba(17, 36, 58, 0.78);
        --panel-border: rgba(46, 204, 113, 0.22);
      }
      .stApp {
        background:
          radial-gradient(1200px 600px at 0% 0%, rgba(46,204,113,0.08), transparent 60%),
          radial-gradient(1000px 600px at 100% 0%, rgba(231,76,60,0.06), transparent 55%),
          linear-gradient(180deg, #06101c 0%, #0a1421 50%, #06101c 100%);
      }
      .block-container { padding-top: 2.2rem; padding-bottom: 2rem; }
      h1, h2, h3 { color: #eaf6ff; letter-spacing: 0.5px; }
      .nav-title {
        font-size: 1.9rem; font-weight: 700; color: #eaf6ff;
        line-height: 1.35; padding-top: 0.15rem; margin-bottom: 0.15rem;
        text-shadow: 0 0 18px rgba(46, 204, 113, 0.45);
        animation: fadeInDown 0.7s ease-out both;
      }
      .nav-sub  {
        color: #9bbed1; font-size: 0.95rem; line-height: 1.45; margin-top: 0;
        animation: fadeInDown 0.9s ease-out both;
      }
      .pulse-dot {
        display: inline-block; width: 10px; height: 10px;
        border-radius: 50%; background: var(--accent-green);
        margin-right: 8px; vertical-align: middle;
        box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7);
        animation: pulse 1.6s infinite;
      }
      .kpi-grid {
        display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px; margin: 10px 0 18px;
      }
      .kpi-card {
        background: var(--panel-bg);
        border: 1px solid var(--panel-border);
        border-radius: 8px;
        padding: 14px 18px;
        backdrop-filter: blur(6px);
        animation: fadeInUp 0.6s ease-out both;
      }
      .kpi-label { color: #9bbed1; font-size: 0.82rem; letter-spacing: 0.4px; }
      .kpi-value { color: #eaf6ff; font-size: 1.7rem; font-weight: 700; margin-top: 4px; }
      .kpi-foot  { color: #9bbed1; font-size: 0.78rem; margin-top: 4px; }
      .kpi-good  .kpi-value { color: var(--accent-green); }
      .kpi-warn  .kpi-value { color: var(--accent-amber); }
      .kpi-bad   .kpi-value { color: var(--accent-red); }
      .legend-row {
        display: flex; gap: 1.4rem; flex-wrap: wrap;
        font-size: 0.9rem; color: #cfe4f3;
        margin: 0.4rem 0 1.0rem;
      }
      .legend-row .dot {
        display: inline-block; width: 12px; height: 12px;
        border-radius: 50%; margin-right: 6px; vertical-align: middle;
      }
      section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1626 0%, #0a1421 100%);
        border-right: 1px solid rgba(46, 204, 113, 0.12);
      }
      section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
      .stTabs [data-baseweb="tab-list"] { gap: 6px; }
      .stTabs [data-baseweb="tab"] {
        background: rgba(17, 36, 58, 0.5);
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
      }
      .stTabs [aria-selected="true"] {
        background: rgba(46, 204, 113, 0.18);
        border-bottom: 2px solid var(--accent-green);
      }
      @keyframes pulse {
        0%   { box-shadow: 0 0 0 0 rgba(46,204,113,0.6); }
        70%  { box-shadow: 0 0 0 14px rgba(46,204,113,0); }
        100% { box-shadow: 0 0 0 0 rgba(46,204,113,0); }
      }
      @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-8px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      @media (max-width: 1100px) {
        .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      }
      @media (max-width: 700px) {
        .kpi-grid { grid-template-columns: 1fr; }
        .nav-title { font-size: 1.45rem; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================================
# Data
# =====================================================================
DATA_PATH = Path(__file__).resolve().parent / "data" / "signal_samples.csv"


@st.cache_data(show_spinner=False)
def _load() -> pd.DataFrame:
    """Load CSV exactly once per cache key; returns the full dataset."""
    return load_signal_samples(DATA_PATH)


full_df = _load()
SPEED_COL = detect_speed_column(full_df)  # "Download_Mbps" for contest data


# =====================================================================
# Sidebar -- live filters
# =====================================================================
with st.sidebar:
    st.markdown(
        "<div class='nav-title' style='font-size:1.1rem;'>"
        "<span class='pulse-dot'></span>态势筛选器</div>",
        unsafe_allow_html=True,
    )
    st.caption("拖动控件即可联动主面板上的地图与图表")

    bands_all = sorted(full_df["Band"].unique().tolist())
    selected_bands = st.multiselect(
        "频段 Band", bands_all, default=bands_all, help="支持多选；清空即过滤为空"
    )

    rsrp_min = float(full_df["RSRP_dBm"].min())
    rsrp_max = float(full_df["RSRP_dBm"].max())
    rsrp_range = st.slider(
        "RSRP 范围 (dBm)",
        min_value=float(np.floor(rsrp_min)),
        max_value=float(np.ceil(rsrp_max)),
        value=(float(np.floor(rsrp_min)), float(np.ceil(rsrp_max))),
        step=1.0,
    )

    terminals_all = sorted(full_df["TerminalType"].unique().tolist())
    selected_terminals = st.multiselect(
        "终端类型 TerminalType", terminals_all, default=terminals_all
    )

    speed_min = float(full_df[SPEED_COL].min())
    speed_max = float(full_df[SPEED_COL].max())
    speed_range = st.slider(
        f"下载速率范围 ({SPEED_COL})",
        min_value=float(np.floor(speed_min)),
        max_value=float(np.ceil(speed_max)),
        value=(float(np.floor(speed_min)), float(np.ceil(speed_max))),
        step=5.0,
    )

    st.divider()
    map_mode = st.radio(
        "地图模式", ("2D 散点", "3D 柱状"), index=1, horizontal=True
    )
    chart_kind = st.radio(
        "频段统计图", ("柱状图", "饼图"), index=0, horizontal=True
    )

    st.divider()
    st.caption(
        "速率字段自动识别：优先匹配 download/throughput/rate/速率，"
        f"找不到则回退到 SINR 或 RSRP。当前使用：**{SPEED_COL}**"
    )


# Apply all filters in one call -- src.filters.apply_filters owns the logic.
df = apply_filters(
    full_df,
    bands=selected_bands,
    rsrp_range=rsrp_range,
    terminal_types=selected_terminals,
    speed_range=speed_range,
    speed_col=SPEED_COL,
)


# =====================================================================
# Header + KPI strip
# =====================================================================
st.markdown(
    "<div class='nav-title'><span class='pulse-dot'></span>"
    "5G 信号态势作战室</div>"
    "<div class='nav-sub'>Code with AI 海选赛 · 进阶关卡 ·"
    " 实时筛选 · 3D 信号柱状 · 数据来源：besa-2026/code-with-ai-contest</div>",
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("当前筛选条件下没有匹配的采样点 — 请放宽筛选器")
    st.stop()


def _kpi_class(rsrp_avg: float) -> str:
    if rsrp_avg > -90:
        return "kpi-good"
    if rsrp_avg < -100:
        return "kpi-bad"
    return "kpi-warn"


excellent = (df["RSRP_dBm"] > -90).sum()
weak = (df["RSRP_dBm"] < -110).sum()
avg_rsrp = float(df["RSRP_dBm"].mean())
avg_speed = float(df[SPEED_COL].mean()) if SPEED_COL in df.columns else float("nan")

kpi_html = f"""
<div class='kpi-grid'>
  <div class='kpi-card'>
    <div class='kpi-label'>采样点</div>
    <div class='kpi-value'>{len(df):,}</div>
    <div class='kpi-foot'>共 {len(full_df):,} 条 · 已筛选</div>
  </div>
  <div class='kpi-card {_kpi_class(avg_rsrp)}'>
    <div class='kpi-label'>平均 RSRP</div>
    <div class='kpi-value'>{avg_rsrp:.1f} dBm</div>
    <div class='kpi-foot'>越大越好 · 阈值 -90 / -110</div>
  </div>
  <div class='kpi-card kpi-good'>
    <div class='kpi-label'>优质点 (&gt;-90 dBm)</div>
    <div class='kpi-value'>{excellent:,}</div>
    <div class='kpi-foot'>占比 {excellent / len(df):.0%}</div>
  </div>
  <div class='kpi-card kpi-bad'>
    <div class='kpi-label'>弱覆盖 (&lt;-110 dBm)</div>
    <div class='kpi-value'>{weak:,}</div>
    <div class='kpi-foot'>占比 {weak / len(df):.0%} · 平均速率 {avg_speed:.0f} Mbps</div>
  </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)


# =====================================================================
# Map -- shared base view + tabbed 2D/3D layers
# =====================================================================
df_colored = attach_color_columns(df)
df_colored["pillar_height"] = normalize_height(df_colored[SPEED_COL].values)
df_colored["radius_m"] = 80  # consistent scatter radius for 2D mode

view_state = pdk.ViewState(
    latitude=float(df["Latitude"].mean()),
    longitude=float(df["Longitude"].mean()),
    zoom=11,
    pitch=45 if map_mode == "3D 柱状" else 0,
    bearing=15 if map_mode == "3D 柱状" else 0,
)

tooltip_html = (
    "<b>CellID</b>: {CellID}<br/>"
    "<b>Band</b>: {Band}<br/>"
    "<b>Terminal</b>: {TerminalType}<br/>"
    "<b>RSRP</b>: {RSRP_dBm} dBm ({rsrp_tier})<br/>"
    "<b>SINR</b>: {SINR_dB} dB<br/>"
    "<b>Download</b>: {Download_Mbps} Mbps"
)

if map_mode == "3D 柱状":
    map_layer = pdk.Layer(
        "ColumnLayer",
        data=df_colored,
        get_position="[Longitude, Latitude]",
        get_elevation="pillar_height",
        elevation_scale=1,
        radius=60,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
        extruded=True,
    )
    sub_caption = (
        f"3D 柱高 = {SPEED_COL} 归一化（80–1500 m），颜色按 RSRP 分级。"
        " 鼠标可拖拽旋转/缩放。"
    )
else:
    map_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_colored,
        get_position="[Longitude, Latitude]",
        get_fill_color="color",
        get_radius="radius_m",
        pickable=True,
        opacity=0.85,
        radius_min_pixels=3,
        radius_max_pixels=18,
    )
    sub_caption = "2D 散点，颜色按 RSRP_dBm 分级。"

st.subheader("🗺️ 信号点地图")
st.caption(sub_caption)
st.pydeck_chart(
    pdk.Deck(
        layers=[map_layer],
        initial_view_state=view_state,
        map_style="dark",
        tooltip={"html": tooltip_html, "style": {"backgroundColor": "#0f1c2e", "color": "#fff"}},
    )
)

# Color-tier legend — uses the same RGBA constants as src.coloring.
def _legend_swatch(rgba):
    return f"rgb({rgba[0]},{rgba[1]},{rgba[2]})"


legend_html = f"""
<div class='legend-row'>
  <span><span class='dot' style='background:{_legend_swatch(COLOR_EXCELLENT)};'></span>
    RSRP &gt; -90 dBm（优）</span>
  <span><span class='dot' style='background:{_legend_swatch(COLOR_GOOD)};'></span>
    -100 ~ -90 dBm（良）</span>
  <span><span class='dot' style='background:{_legend_swatch(COLOR_FAIR)};'></span>
    -110 ~ -100 dBm（中）</span>
  <span><span class='dot' style='background:{_legend_swatch(COLOR_POOR)};'></span>
    RSRP &lt; -110 dBm（弱）</span>
</div>
"""
st.markdown(legend_html, unsafe_allow_html=True)


# =====================================================================
# Charts row
# =====================================================================
st.subheader("📊 数据概览")
left, right = st.columns(2)

with left:
    st.markdown("**各频段基站数量**")
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
            band_counts, names="Band", values="基站数量",
            hole=0.45, template="plotly_dark",
        )
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=320)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("**终端类型构成**")
    term_counts = (
        df.groupby("TerminalType")
        .size()
        .reset_index(name="数量")
        .sort_values("数量", ascending=False)
    )
    fig2 = px.pie(
        term_counts,
        names="TerminalType",
        values="数量",
        hole=0.45,
        template="plotly_dark",
        color_discrete_sequence=px.colors.sequential.Tealgrn,
    )
    fig2.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=320)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("**RSRP 分布与速率散点**")
left2, right2 = st.columns(2)
with left2:
    fig3 = px.histogram(
        df, x="RSRP_dBm", nbins=30, template="plotly_dark",
        color_discrete_sequence=["#2ecc71"],
    )
    fig3.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=300)
    st.plotly_chart(fig3, use_container_width=True)
with right2:
    fig4 = px.scatter(
        df, x="RSRP_dBm", y=SPEED_COL, color="Band",
        template="plotly_dark", opacity=0.75,
    )
    fig4.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=300)
    st.plotly_chart(fig4, use_container_width=True)


# =====================================================================
# Data table preview
# =====================================================================
with st.expander("查看筛选后的明细数据 (前 100 行)"):
    st.dataframe(
        df.head(100).reset_index(drop=True),
        use_container_width=True,
    )

st.caption(
    "Tip: 修改左侧任意筛选器，地图 / KPI / 图表会实时刷新。"
    " 切换 2D / 3D 模式可以分别强调覆盖区域和下载速率。"
)

"""RSRP-driven color tiers for the map and KPI cards.

The contest spec dictates: ``RSRP > -90 dBm`` is green (excellent), ``RSRP <
-110 dBm`` is red (poor), everything in between is a yellow-to-orange
gradient (fair-to-marginal). This module owns that mapping so both the
pydeck layer and the data table use identical colors.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd

# RGBA tuples chosen for the dark "war room" theme.
COLOR_EXCELLENT: Tuple[int, int, int, int] = (46, 204, 113, 220)   # vivid green
COLOR_GOOD: Tuple[int, int, int, int] = (241, 196, 15, 220)        # warm yellow
COLOR_FAIR: Tuple[int, int, int, int] = (230, 126, 34, 220)        # orange
COLOR_POOR: Tuple[int, int, int, int] = (231, 76, 60, 220)         # red

THRESHOLD_EXCELLENT = -90.0
THRESHOLD_POOR = -110.0
THRESHOLD_MID = -100.0  # yellow / orange split inside the middle band


def rsrp_color(rsrp):
    """Return an RGBA tuple for a single RSRP value.

    NaN inputs are treated as "poor" so they remain visible but flagged.
    """
    if rsrp is None or (isinstance(rsrp, float) and np.isnan(rsrp)):
        return COLOR_POOR
    if rsrp > THRESHOLD_EXCELLENT:
        return COLOR_EXCELLENT
    if rsrp < THRESHOLD_POOR:
        return COLOR_POOR
    if rsrp >= THRESHOLD_MID:
        return COLOR_GOOD
    return COLOR_FAIR


def rsrp_tier_label(rsrp) -> str:
    """Human-readable tier label, in Chinese, for charts and tables."""
    if rsrp is None or (isinstance(rsrp, float) and np.isnan(rsrp)):
        return "弱覆盖"
    if rsrp > THRESHOLD_EXCELLENT:
        return "优"
    if rsrp < THRESHOLD_POOR:
        return "弱覆盖"
    if rsrp >= THRESHOLD_MID:
        return "良"
    return "中"


def attach_color_columns(df: pd.DataFrame, rsrp_col: str = "RSRP_dBm") -> pd.DataFrame:
    """Add color components and ``rsrp_tier`` columns to a copy of ``df``.

    pydeck expects color components either as separate columns or as a
    list-valued field, so we expose both forms: scalar RGBA components
    plus a ``color`` list.
    """
    out = df.copy()
    colors = out[rsrp_col].apply(rsrp_color)
    out["color_r"] = colors.apply(lambda c: c[0])
    out["color_g"] = colors.apply(lambda c: c[1])
    out["color_b"] = colors.apply(lambda c: c[2])
    out["color_a"] = colors.apply(lambda c: c[3])
    out["color"] = colors.apply(list)
    out["rsrp_tier"] = out[rsrp_col].apply(rsrp_tier_label)
    return out

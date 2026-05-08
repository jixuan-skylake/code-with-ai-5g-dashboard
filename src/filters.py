"""Sidebar filter logic, kept as pure functions for testability."""

from __future__ import annotations

from typing import Iterable, Optional, Tuple

import pandas as pd


def apply_filters(
    df: pd.DataFrame,
    bands: Optional[Iterable] = None,
    rsrp_range: Optional[Tuple[float, float]] = None,
    terminal_types: Optional[Iterable] = None,
    speed_range: Optional[Tuple[float, float]] = None,
    speed_col: str = "Download_Mbps",
) -> pd.DataFrame:
    """Filter the signal dataframe according to sidebar selections.

    Parameters
    ----------
    df:
        Source dataframe (already loaded and cleaned).
    bands:
        Iterable of allowed Band values; ``None`` means no band filter.
        An empty iterable returns an empty dataframe (the user explicitly
        deselected everything).
    rsrp_range:
        ``(low, high)`` inclusive bounds on ``RSRP_dBm``.
    terminal_types:
        Iterable of allowed TerminalType values, with the same empty-vs-None
        semantics as ``bands``.
    speed_range:
        Optional inclusive bounds on the speed column.
    speed_col:
        Column name to use for ``speed_range`` filtering.
    """
    out = df

    if bands is not None:
        bands_list = list(bands)
        out = out[out["Band"].isin(bands_list)]

    if rsrp_range is not None:
        low, high = rsrp_range
        out = out[(out["RSRP_dBm"] >= low) & (out["RSRP_dBm"] <= high)]

    if terminal_types is not None:
        tt_list = list(terminal_types)
        out = out[out["TerminalType"].isin(tt_list)]

    if speed_range is not None and speed_col in out.columns:
        low, high = speed_range
        out = out[(out[speed_col] >= low) & (out[speed_col] <= high)]

    return out.reset_index(drop=True)

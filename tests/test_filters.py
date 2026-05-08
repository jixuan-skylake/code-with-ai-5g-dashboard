"""Tests for ``src.filters.apply_filters``."""

from __future__ import annotations

import pandas as pd
import pytest

from src.filters import apply_filters


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Latitude":     [31.20, 31.21, 31.22, 31.23, 31.24],
            "Longitude":    [121.40, 121.41, 121.42, 121.43, 121.44],
            "CellID":       [1, 2, 3, 4, 5],
            "Band":         ["n78", "n78", "n28", "n41", "n28"],
            "RSRP_dBm":     [-85.0, -95.0, -105.0, -118.0, -75.0],
            "SINR_dB":      [20.0, 12.0, 5.0, -2.0, 25.0],
            "TerminalType": ["Smartphone", "Smartphone", "CPE", "IoT", "CPE"],
            "Download_Mbps": [800.0, 250.0, 60.0, 5.0, 950.0],
        }
    )


def test_no_filters_returns_full_df(sample_df: pd.DataFrame):
    out = apply_filters(sample_df)
    assert len(out) == len(sample_df)


def test_band_filter(sample_df: pd.DataFrame):
    out = apply_filters(sample_df, bands=["n78"])
    assert set(out["Band"].unique()) == {"n78"}
    assert len(out) == 2


def test_empty_band_returns_empty(sample_df: pd.DataFrame):
    """An explicitly empty multiselect must yield an empty dataframe."""
    out = apply_filters(sample_df, bands=[])
    assert len(out) == 0


def test_rsrp_range_inclusive(sample_df: pd.DataFrame):
    out = apply_filters(sample_df, rsrp_range=(-105, -85))
    assert set(out["CellID"]) == {1, 2, 3}


def test_terminal_type_filter(sample_df: pd.DataFrame):
    out = apply_filters(sample_df, terminal_types=["CPE"])
    assert set(out["TerminalType"].unique()) == {"CPE"}
    assert len(out) == 2


def test_combined_filters_intersect(sample_df: pd.DataFrame):
    out = apply_filters(
        sample_df,
        bands=["n78", "n28"],
        rsrp_range=(-100, -80),
        terminal_types=["Smartphone", "CPE"],
    )
    assert set(out["CellID"]) == {1, 2}


def test_speed_range_filter(sample_df: pd.DataFrame):
    out = apply_filters(sample_df, speed_range=(100, 900), speed_col="Download_Mbps")
    assert set(out["CellID"]) == {1, 2}


def test_speed_range_skipped_when_column_missing():
    df = pd.DataFrame({"Band": ["n78"], "RSRP_dBm": [-90]})
    out = apply_filters(df, speed_range=(0, 100), speed_col="Download_Mbps")
    assert len(out) == 1


def test_filters_do_not_mutate_input(sample_df: pd.DataFrame):
    snapshot = sample_df.copy()
    _ = apply_filters(sample_df, bands=["n78"], rsrp_range=(-100, -80))
    pd.testing.assert_frame_equal(sample_df, snapshot)

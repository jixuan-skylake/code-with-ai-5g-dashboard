"""Tests for ``src.coloring`` -- the RSRP tiering logic."""

from __future__ import annotations

import math

import pandas as pd

from src.coloring import (
    COLOR_EXCELLENT,
    COLOR_FAIR,
    COLOR_GOOD,
    COLOR_POOR,
    attach_color_columns,
    rsrp_color,
    rsrp_tier_label,
)


def test_excellent_above_minus_90():
    assert rsrp_color(-50) == COLOR_EXCELLENT
    assert rsrp_color(-89.9) == COLOR_EXCELLENT


def test_poor_below_minus_110():
    assert rsrp_color(-130) == COLOR_POOR
    assert rsrp_color(-110.1) == COLOR_POOR


def test_good_band_minus_100_to_minus_90_inclusive_lower():
    assert rsrp_color(-90) == COLOR_GOOD
    assert rsrp_color(-95) == COLOR_GOOD
    assert rsrp_color(-100) == COLOR_GOOD


def test_fair_band_minus_110_to_minus_100():
    assert rsrp_color(-100.1) == COLOR_FAIR
    assert rsrp_color(-105) == COLOR_FAIR
    assert rsrp_color(-110) == COLOR_FAIR


def test_nan_rsrp_treated_as_poor():
    assert rsrp_color(float("nan")) == COLOR_POOR
    assert rsrp_color(None) == COLOR_POOR


def test_rsrp_tier_label_chinese():
    assert rsrp_tier_label(-80) == "优"
    assert rsrp_tier_label(-95) == "良"
    assert rsrp_tier_label(-105) == "中"
    assert rsrp_tier_label(-115) == "弱覆盖"
    assert rsrp_tier_label(math.nan) == "弱覆盖"


def test_attach_color_columns_adds_expected_fields():
    df = pd.DataFrame({"RSRP_dBm": [-80, -95, -105, -115]})
    out = attach_color_columns(df)

    for col in ("color_r", "color_g", "color_b", "color_a", "color", "rsrp_tier"):
        assert col in out.columns

    assert (out.loc[0, "color_r"], out.loc[0, "color_g"], out.loc[0, "color_b"]) == (
        COLOR_EXCELLENT[0],
        COLOR_EXCELLENT[1],
        COLOR_EXCELLENT[2],
    )
    assert isinstance(out.loc[0, "color"], list)
    assert len(out.loc[0, "color"]) == 4

    assert out["rsrp_tier"].tolist() == ["优", "良", "中", "弱覆盖"]


def test_attach_color_columns_does_not_mutate_input():
    df = pd.DataFrame({"RSRP_dBm": [-80, -100]})
    snapshot = df.copy()
    _ = attach_color_columns(df)
    pd.testing.assert_frame_equal(df, snapshot)

"""Tests for ``src.heights.normalize_height``."""

from __future__ import annotations

import math

import numpy as np
import pytest

from src.heights import DEFAULT_MAX_HEIGHT, DEFAULT_MIN_HEIGHT, normalize_height


def test_endpoints_map_to_min_and_max():
    out = normalize_height([0, 100])
    assert out[0] == pytest.approx(DEFAULT_MIN_HEIGHT)
    assert out[1] == pytest.approx(DEFAULT_MAX_HEIGHT)


def test_linear_interpolation_in_between():
    out = normalize_height([0, 50, 100], min_height=0.0, max_height=100.0)
    assert out.tolist() == [0.0, 50.0, 100.0]


def test_constant_input_returns_midpoint():
    """Degenerate flat input must not divide by zero."""
    out = normalize_height([7, 7, 7], min_height=10.0, max_height=20.0)
    midpoint = 15.0
    assert np.allclose(out, midpoint)


def test_nan_inputs_clamped_to_min_height():
    out = normalize_height([math.nan, 0, 100], min_height=10.0, max_height=110.0)
    assert out[0] == 10.0
    assert out[1] == pytest.approx(10.0)
    assert out[2] == pytest.approx(110.0)


def test_all_nan_returns_all_min_height():
    out = normalize_height([math.nan, math.nan])
    assert (out == DEFAULT_MIN_HEIGHT).all()


def test_empty_input_returns_empty_array():
    out = normalize_height([])
    assert out.size == 0


def test_invalid_height_bounds_raise():
    with pytest.raises(ValueError):
        normalize_height([0, 1], min_height=100.0, max_height=50.0)


def test_custom_height_bounds_respected():
    out = normalize_height([0, 5, 10], min_height=200.0, max_height=2000.0)
    assert out[0] == pytest.approx(200.0)
    assert out[-1] == pytest.approx(2000.0)
    assert out.min() >= 200.0
    assert out.max() <= 2000.0

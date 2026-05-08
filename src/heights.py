"""3D pillar height normalization for the pydeck ColumnLayer."""

from __future__ import annotations

from typing import Iterable

import numpy as np

# Defaults chosen empirically for the Shanghai Lat/Lon span in the contest
# data: 1.5 km tall pillars are visible without dwarfing the basemap.
DEFAULT_MIN_HEIGHT = 80.0
DEFAULT_MAX_HEIGHT = 1500.0


def normalize_height(
    values: Iterable,
    min_height: float = DEFAULT_MIN_HEIGHT,
    max_height: float = DEFAULT_MAX_HEIGHT,
) -> np.ndarray:
    """Linearly rescale ``values`` into ``[min_height, max_height]``.

    NaN values in the input are mapped to ``min_height`` so the corresponding
    pillars still render (just short). When all values collapse to a single
    number, every pillar gets the midpoint height -- this avoids the
    degenerate "everything is max" output of dividing by zero range.
    """
    if max_height <= min_height:
        raise ValueError(
            f"max_height ({max_height}) must be greater than min_height ({min_height})"
        )

    arr = np.array(list(values), dtype=float)
    if arr.size == 0:
        return arr

    finite_mask = np.isfinite(arr)
    if not finite_mask.any():
        return np.full_like(arr, min_height)

    finite = arr[finite_mask]
    lo, hi = float(finite.min()), float(finite.max())

    if hi == lo:
        midpoint = (min_height + max_height) / 2.0
        return np.full_like(arr, midpoint)

    scaled = np.where(
        finite_mask,
        min_height + (arr - lo) / (hi - lo) * (max_height - min_height),
        min_height,
    )
    return scaled

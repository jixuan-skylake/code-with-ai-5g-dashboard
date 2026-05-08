"""Drag-continuous range slider as a Streamlit custom component.

Why this exists
---------------
Streamlit's native ``st.slider`` is a BaseWeb component that only emits
its ``widgetStateRequest`` (the message that triggers a Python rerun)
on slider **change-end** -- mouse-up or blur. During the drag itself
the value updates locally in the React component but Python never
sees the intermediate values, so the map / KPI / charts only refresh
when the user releases the handle. The contest's advanced-level rule
is the opposite: "拖动筛选器时右侧地图和图表必须实时更新".

The fix is a small custom component that uses an HTML
``<input type="range">`` (whose ``input`` event fires every frame the
value changes during a drag) and wires that event back to Streamlit
through the documented component-bridge protocol:

* ``streamlit:componentReady`` -- on iframe load, so Streamlit sends
  ``streamlit:render`` with our args.
* ``streamlit:setComponentValue`` -- emitted every ``input`` event so
  Python sees the drag value continuously.
* ``streamlit:setFrameHeight`` -- so the iframe sizes itself.

Frontend lives in ``frontend/live_range_slider/index.html`` (vanilla
JS / CSS, no CDN, no npm build step). ``declare_component(path=...)``
points to that directory so Streamlit serves the file from local disk
on every reload.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import streamlit.components.v1 as components

_FRONTEND_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "frontend"
    / "live_range_slider"
)

# ``declare_component`` is module-level so Streamlit only does the
# disk-serve handshake once per process; calling the resulting function
# is cheap on subsequent reruns.
_component_func = components.declare_component(
    "live_range_slider",
    path=str(_FRONTEND_DIR),
)


def _coerce_float(value, fallback: float) -> float:
    """Best-effort float coercion -- handles ints, numeric strings, and
    occasional ``None``-shaped slop from postMessage."""
    if value is None:
        return float(fallback)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _normalize_range(
    value, min_v: float, max_v: float
) -> Tuple[float, float]:
    """Coerce the iframe payload into a clamped, ordered ``(low, high)`` tuple.

    The component normally posts back ``{"low": x, "high": y}``. We also
    accept 2-tuples / 2-lists for forward compatibility, treat ``None``
    as "no message yet" (returns the full range), and reject anything
    else with ``TypeError`` so silent drift can't mask a regression.
    """
    if value is None:
        return (float(min_v), float(max_v))

    if isinstance(value, dict):
        lo = _coerce_float(value.get("low"), min_v)
        hi = _coerce_float(value.get("high"), max_v)
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        lo = _coerce_float(value[0], min_v)
        hi = _coerce_float(value[1], max_v)
    else:
        raise TypeError(f"unexpected component value: {value!r}")

    lo = max(float(min_v), min(lo, float(max_v)))
    hi = max(float(min_v), min(hi, float(max_v)))
    if lo > hi:
        lo, hi = hi, lo
    return (lo, hi)


def live_range_slider(
    label: str,
    min_value: float,
    max_value: float,
    value: Optional[Tuple[float, float]] = None,
    step: float = 1.0,
    key: Optional[str] = None,
) -> Tuple[float, float]:
    """Render a drag-continuous range slider.

    Behaves like ``st.slider`` for ranges, but emits a Python rerun on
    every HTML ``input`` event (i.e. continuously while the user is
    dragging the handle). Accepts the same ``label``/``min_value``/
    ``max_value``/``value``/``step``/``key`` you'd pass to ``st.slider``.

    Returns ``(low, high)`` as a tuple of floats.
    """
    if value is None:
        value = (min_value, max_value)
    lo0, hi0 = float(value[0]), float(value[1])

    raw = _component_func(
        label=label,
        min=float(min_value),
        max=float(max_value),
        low=lo0,
        high=hi0,
        step=float(step),
        # ``default`` is what Streamlit returns on the very first render
        # before the iframe has had a chance to post anything back.
        default={"low": lo0, "high": hi0},
        key=key,
    )
    return _normalize_range(raw, min_value, max_value)

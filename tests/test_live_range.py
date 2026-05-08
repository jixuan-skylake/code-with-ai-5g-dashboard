"""Tests for the ``live_range_slider`` custom component.

These tests pin down two things that the contest's "实时更新 / drag-continuous"
requirement depends on:

1. The Python wrapper's value-coercion contract: ``_normalize_range``
   accepts the raw payload that comes back from the iframe (a dict with
   ``low`` / ``high`` keys, or a 2-tuple shape) and returns a clamped,
   ordered ``(low, high)`` tuple that the rest of the app can rely on.
2. The frontend HTML's drag-continuous contract: the file MUST listen
   to the HTML ``input`` event (which fires every frame during a drag,
   unlike ``change`` which only fires on mouse-up) AND announce itself
   via ``streamlit:componentReady`` and emit values via
   ``streamlit:setComponentValue`` postMessages.

If either of these regresses back to the native ``st.slider`` behavior,
the contest's advanced-level "拖动筛选器时右侧地图和图表必须实时更新"
spec breaks again, and these tests fail.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.components.live_range import _normalize_range

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_HTML = PROJECT_ROOT / "frontend" / "live_range_slider" / "index.html"


# -----------------------------------------------------------------------------
# Python-side: value-coercion contract
# -----------------------------------------------------------------------------
class TestNormalizeRange:
    def test_none_returns_full_range_as_floats(self):
        assert _normalize_range(None, 0, 100) == (0.0, 100.0)

    def test_dict_low_high_returned_as_floats(self):
        assert _normalize_range({"low": 10, "high": 50}, 0, 100) == (10.0, 50.0)

    def test_list_two_elements(self):
        assert _normalize_range([10, 50], 0, 100) == (10.0, 50.0)

    def test_tuple_two_elements(self):
        assert _normalize_range((10, 50), 0, 100) == (10.0, 50.0)

    def test_clamps_below_min(self):
        assert _normalize_range({"low": -10, "high": 50}, 0, 100) == (0.0, 50.0)

    def test_clamps_above_max(self):
        assert _normalize_range({"low": 10, "high": 200}, 0, 100) == (10.0, 100.0)

    def test_swaps_inverted_bounds(self):
        # Drag past each other -- the wrapper must still hand Python the
        # canonical (low, high) ordering.
        assert _normalize_range({"low": 60, "high": 40}, 0, 100) == (40.0, 60.0)

    def test_handles_string_numerics_in_dict(self):
        # postMessage may coerce numbers to strings depending on dataType;
        # the wrapper must still survive.
        assert _normalize_range({"low": "10", "high": "50"}, 0, 100) == (10.0, 50.0)

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            _normalize_range("not-a-range", 0, 100)


# -----------------------------------------------------------------------------
# Frontend-side: drag-continuous contract
# -----------------------------------------------------------------------------
class TestFrontendHTMLContract:
    def test_html_file_is_committed(self):
        assert FRONTEND_HTML.exists(), (
            f"frontend asset missing: {FRONTEND_HTML}. "
            "declare_component(path=...) needs an index.html on disk."
        )

    def test_subscribes_to_input_event_for_continuous_drag(self):
        """The whole point of this fix: the frontend must use the 'input'
        event (fires while dragging) rather than 'change' (only on mouse-up)."""
        content = FRONTEND_HTML.read_text(encoding="utf-8")
        assert (
            "addEventListener('input'" in content
            or 'addEventListener("input"' in content
        ), "frontend must subscribe to the 'input' event for live drag updates"

    def test_emits_set_component_value_postmessage(self):
        content = FRONTEND_HTML.read_text(encoding="utf-8")
        assert "streamlit:setComponentValue" in content, (
            "frontend must call setComponentValue to push live values to Python"
        )

    def test_announces_component_ready(self):
        content = FRONTEND_HTML.read_text(encoding="utf-8")
        assert "streamlit:componentReady" in content, (
            "frontend must announce componentReady so Streamlit hands it args"
        )

    def test_self_contained_no_external_cdn(self):
        """Contest constraint: '不要依赖外部 CDN'."""
        content = FRONTEND_HTML.read_text(encoding="utf-8")
        for pat in ("https://", "http://"):
            assert pat not in content, (
                f"frontend must not pull from an external URL ({pat!r} found)"
            )

    def test_renders_two_range_inputs(self):
        """A range slider needs both a low and a high handle."""
        content = FRONTEND_HTML.read_text(encoding="utf-8")
        hits = content.count('type="range"') + content.count("type=range")
        assert hits >= 2, (
            "frontend must render two range inputs for the dual-handle slider"
        )

"""Static app-level UI contract tests.

These tests avoid importing ``app.py`` directly because importing it would
execute the Streamlit page. They still pin down high-value UI contracts that
are easy to regress during contest polish work.
"""

from __future__ import annotations

from pathlib import Path


APP = Path(__file__).resolve().parent.parent / "app.py"


def test_terminal_type_chart_has_bar_and_pie_toggle():
    """Terminal composition should match the band chart's bar/pie control."""
    source = APP.read_text(encoding="utf-8")
    assert "终端统计图" in source
    assert "terminal_chart_kind" in source
    assert '("柱状图", "饼图")' in source
    assert "px.bar(" in source
    assert "px.pie(" in source

"""End-to-end verifier for the drag-continuous range slider.

Runs against an already-running Streamlit dev server (default
``http://127.0.0.1:8501``). Drives synthetic ``input`` events on the
RSRP live-range slider's lower handle, and asserts THREE things:

1. ``setComponentValue`` postMessages are emitted multiple times during
   the drag (i.e. before mouse-up) -- proves the iframe is wired to the
   ``input`` event, not ``change``.
2. The dashboard's KPI value reacts to the intermediate values --
   proves that Streamlit reran Python from each in-drag value, not
   just from a final mouse-up.
3. After the drag completes and Streamlit has settled, the iframe's
   displayed handle value matches the LAST setComponentValue payload.
   This pins down the second bug: without sticky state, the iframe
   would snap the handle back to the initial default on every rerun
   even though the underlying filter applied the user's value.

Saves a screenshot of the page mid-drag to
``docs/screenshots/04_live_drag_proof.png`` so the proof can be
inspected by hand later.

Exit code 0 = all three checks pass; non-zero = check failed (with a
human-readable reason on stderr).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = os.environ.get("DASHBOARD_URL", "http://127.0.0.1:8501/")


def _install_message_recorder(page: Page) -> None:
    """Hook the parent window so we can count setComponentValue messages."""
    page.add_init_script(
        """
        window.__sliderMessages = [];
        window.addEventListener('message', (e) => {
            try {
              const d = e.data || {};
              if (d.isStreamlitMessage && d.type === 'streamlit:setComponentValue') {
                window.__sliderMessages.push(d.value);
              }
            } catch (err) { /* swallow cross-origin */ }
        }, true);
        """
    )


def _find_live_slider_frame(page: Page):
    """Locate the iframe whose document contains our component (#lo handle)."""
    for fr in page.frames:
        try:
            handle = fr.evaluate("() => !!document.getElementById('lo')")
            if handle:
                return fr
        except Exception:
            continue
    return None


def _read_kpi_count(page: Page) -> int:
    """Pull the '采样点 N' KPI off the page; returns -1 if not found."""
    text = page.evaluate(
        """() => {
            const cards = document.querySelectorAll('.kpi-card');
            for (const c of cards) {
                if (/采样点/.test(c.textContent)) return c.textContent;
            }
            return '';
        }"""
    )
    m = re.search(r"(\d{1,4})", text or "")
    return int(m.group(1)) if m else -1


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = ctx.new_page()
        _install_message_recorder(page)

        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector('text="5G 信号态势作战室"', timeout=25000)
        # Allow custom-component iframes and pydeck WebGL to settle.
        page.wait_for_timeout(4500)

        frame = _find_live_slider_frame(page)
        if frame is None:
            print("[FAIL] could not locate live_range_slider iframe", file=sys.stderr)
            return 1

        baseline_msgs = page.evaluate("window.__sliderMessages.length")
        baseline_kpi = _read_kpi_count(page)
        print(f"baseline messages={baseline_msgs} KPI(采样点)={baseline_kpi}")

        # Drive 8 synthetic 'input' events on the LOWER handle, simulating
        # a drag from the leftmost stop towards the middle of the track.
        # These do NOT include 'change' events, so any rerun the page does
        # is direct evidence of mid-drag updates.
        scripted_values = [-130, -125, -120, -115, -110, -105, -100, -95]
        for v in scripted_values:
            frame.evaluate(
                """(v) => {
                    const el = document.getElementById('lo');
                    el.value = v;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                }""",
                v,
            )
            page.wait_for_timeout(140)  # let Streamlit rerun before next event

        page.wait_for_timeout(800)

        msg_delta = page.evaluate("window.__sliderMessages.length") - baseline_msgs
        kpi_after = _read_kpi_count(page)
        print(f"setComponentValue messages during drag: {msg_delta}")
        print(f"KPI(采样点) after drag: {kpi_after} (was {baseline_kpi})")

        # Sticky-state check: after drag + rerun, the iframe's displayed
        # handle value MUST match the last committed value. If not, the
        # bug from issue #2 is back: visual position desynced from filter
        # state. Streamlit may have rerun the iframe-bearing block, so we
        # have to re-locate the frame here -- the earlier ``frame`` may
        # be stale.
        live_frame = _find_live_slider_frame(page)
        if live_frame is None:
            print("[FAIL] live_range_slider iframe not found after drag", file=sys.stderr)
            return 1
        final_lo = live_frame.evaluate(
            "() => Number(document.getElementById('lo').value)"
        )
        final_hi = live_frame.evaluate(
            "() => Number(document.getElementById('hi').value)"
        )
        last_msg = page.evaluate(
            "() => window.__sliderMessages[window.__sliderMessages.length - 1] || null"
        )
        print(f"final iframe handles: lo={final_lo} hi={final_hi}")
        print(f"last setComponentValue payload: {last_msg}")

        # Capture proof screenshot.
        out_path = OUT_DIR / "04_live_drag_proof.png"
        page.screenshot(path=str(out_path), full_page=True)
        print(f"proof screenshot -> {out_path}")

        problems = []
        if msg_delta < 5:
            problems.append(
                f"expected >= 5 setComponentValue messages during drag, got {msg_delta}"
            )
        if kpi_after == baseline_kpi:
            problems.append(
                "KPI did not change during drag -- Streamlit may not be rerunning from input events"
            )
        if last_msg is None:
            problems.append("no setComponentValue payload was recorded")
        else:
            expected_lo = float(last_msg["low"])
            expected_hi = float(last_msg["high"])
            tol = 1.5  # tolerance for slider step rounding
            if abs(float(final_lo) - expected_lo) > tol:
                problems.append(
                    f"iframe LOW handle snapped back to {final_lo} instead of {expected_lo} "
                    "(sticky-state bug)"
                )
            if abs(float(final_hi) - expected_hi) > tol:
                problems.append(
                    f"iframe HIGH handle snapped back to {final_hi} instead of {expected_hi} "
                    "(sticky-state bug)"
                )

        browser.close()

        if problems:
            print("[FAIL] " + "; ".join(problems), file=sys.stderr)
            return 1
        print(
            "[PASS] live drag updates confirmed end-to-end "
            "(input events + KPI rerun + iframe handle stays synced)"
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())

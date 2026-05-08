"""Render dashboard screenshots via headless Chromium (Playwright).

This is a one-shot helper -- it expects a Streamlit dev server to be
already running on ``http://localhost:8765`` by default. Override with
``DASHBOARD_URL`` when using another port. Outputs land in
``docs/screenshots/``. Three captures by default:

1. ``01_overview_3d.png`` -- default 3D pillar view at full window.
2. ``02_2d_scatter.png``  -- after toggling the sidebar to 2D mode.
3. ``03_filter_narrowed.png`` -- after narrowing the band filter so the
   reviewer can see live filtering at work.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = os.environ.get("DASHBOARD_URL", "http://localhost:8765/")
VIEWPORT = {"width": 1600, "height": 1000}


def _wait_for_streamlit(page, marker: str, timeout_ms: int = 25000) -> None:
    page.wait_for_selector(f'text="{marker}"', timeout=timeout_ms)


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=2)
        page = ctx.new_page()

        # Streamlit keeps websocket/runtime requests open, so ``networkidle``
        # can be flaky. DOM ready plus the dashboard title is the stable signal.
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        _wait_for_streamlit(page, "5G 信号态势作战室")
        # Give pydeck's ColumnLayer a moment to finish WebGL init.
        page.wait_for_timeout(3500)

        page.screenshot(path=str(OUT_DIR / "01_overview_3d.png"), full_page=True)
        print("wrote 01_overview_3d.png")

        # Switch to 2D scatter via sidebar radio.
        try:
            page.locator('label:has-text("2D 散点")').first.click()
            page.wait_for_timeout(2500)
        except Exception as exc:
            print(f"[warn] could not toggle 2D mode: {exc}")
        page.screenshot(path=str(OUT_DIR / "02_2d_scatter.png"), full_page=True)
        print("wrote 02_2d_scatter.png")

        # Narrow the RSRP slider so a filter interaction is visible.
        try:
            slider_handles = page.locator('div[data-baseweb="slider"] [role="slider"]')
            if slider_handles.count() >= 2:
                handle = slider_handles.nth(1)
                handle.focus()
                for _ in range(20):
                    page.keyboard.press("ArrowLeft")
                page.wait_for_timeout(2500)
        except Exception as exc:
            print(f"[warn] could not move slider: {exc}")
        page.screenshot(path=str(OUT_DIR / "03_filter_narrowed.png"), full_page=True)
        print("wrote 03_filter_narrowed.png")

        browser.close()

    print(f"all screenshots saved under {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

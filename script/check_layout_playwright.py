from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from playwright.sync_api import sync_playwright


@dataclass
class Rect:
    left: float
    right: float
    top: float
    bottom: float
    width: float
    height: float


def _as_rect(obj: Optional[Dict[str, Any]]) -> Optional[Rect]:
    if not obj:
        return None
    return Rect(
        left=float(obj["left"]),
        right=float(obj["right"]),
        top=float(obj["top"]),
        bottom=float(obj["bottom"]),
        width=float(obj["width"]),
        height=float(obj["height"]),
    )


def main() -> None:
    url = "http://localhost:5000/?_t=3"
    viewport = {"width": 1440, "height": 900}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=viewport)
        page.goto(url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=30000)
        # Give animations (GSAP/ApexCharts) time to settle
        page.wait_for_timeout(2000)

        info = page.evaluate(
            """
() => {
  const get = (sel) => document.querySelector(sel);
  const rect = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {left:r.left, right:r.right, top:r.top, bottom:r.bottom, width:r.width, height:r.height};
  };
    const closestRect = (el, sel) => {
        if (!el) return null;
        const found = el.closest(sel);
        return rect(found);
    };
  const sidebar = rect(get('#sidebar'));
  const main = rect(get('#main-content'));
  const charts = ['#chart-distribution', '#chart-trends', '#chart-factories', '#chart-top10'];
    const chartRects = charts.map(sel => {
        const el = get(sel);
        const panelEl = el ? el.closest('.glass-panel') : null;
        const containerEl = el ? el.closest('.chart-container, .chart-container-sm, .chart-container-lg') : null;
        const parentChain = [];
        let cur = el;
        for (let i = 0; i < 8 && cur; i++) {
            parentChain.push({
                tag: cur.tagName,
                id: cur.id || null,
                cls: cur.className || null
            });
            cur = cur.parentElement;
        }
        return {
            sel,
            rect: rect(el),
            container: rect(containerEl),
            panel: rect(panelEl),
            inMain: !!(el && el.closest('#main-content')),
            panelInMain: !!(panelEl && panelEl.closest('#main-content')),
            containerInMain: !!(containerEl && containerEl.closest('#main-content')),
            panelClass: panelEl ? panelEl.className : null,
            panelId: panelEl ? panelEl.id : null,
            parentChain
        };
    });
  return {
    viewport: {w: window.innerWidth, h: window.innerHeight},
    sidebar,
    main,
    chartRects
  };
}
"""
        )
        browser.close()

    vw = int(info["viewport"]["w"])
    vh = int(info["viewport"]["h"])
    sidebar = _as_rect(info.get("sidebar"))
    main_rect = _as_rect(info.get("main"))

    print(f"viewport: {vw}x{vh}")
    print(f"sidebar: {sidebar}")
    print(f"main:    {main_rect}")

    issues: List[Tuple[str, str]] = []
    for c in info.get("chartRects", []):
        sel = c.get("sel")
        # Prefer measuring the visible container/panel to avoid false positives
        r = _as_rect(c.get("panel")) or _as_rect(c.get("container")) or _as_rect(c.get("rect"))
        if not r:
            issues.append((sel, "missing"))
            continue

        if sel in {"#chart-distribution", "#chart-trends"}:
            print(
                f"debug {sel}: inMain={c.get('inMain')} panelInMain={c.get('panelInMain')} containerInMain={c.get('containerInMain')} rectUsed={r}"
            )
            if not c.get('inMain'):
                print(f"parentChain {sel}: {c.get('parentChain')}")

        if sidebar and r.left < (sidebar.right - 1):
            issues.append((sel, f"overlaps sidebar (chart.left={r.left:.1f} < sidebar.right={sidebar.right:.1f})"))
        if r.right > vw + 1:
            issues.append((sel, f"overflows viewport (chart.right={r.right:.1f} > vw={vw})"))
        if main_rect and r.left < (main_rect.left - 1):
            issues.append((sel, f"escapes main-content left (chart.left={r.left:.1f} < main.left={main_rect.left:.1f})"))

    print("issues:")
    if issues:
        for sel, msg in issues:
            print(f"- {sel}: {msg}")
    else:
        print("- none")


if __name__ == "__main__":
    main()

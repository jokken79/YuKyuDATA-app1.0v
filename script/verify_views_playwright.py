from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from playwright.sync_api import sync_playwright


@dataclass
class Rect:
    left: float
    right: float
    top: float
    bottom: float
    width: float
    height: float


class Viewport(TypedDict):
    width: int
    height: int


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


def _check_overlap(sidebar: Optional[Rect], main: Optional[Rect], rect: Rect, vw: int) -> List[str]:
    issues: List[str] = []
    if sidebar and rect.left < sidebar.right - 1:
        issues.append(f"overlaps sidebar (left={rect.left:.1f} < sidebar.right={sidebar.right:.1f})")
    if main and rect.left < main.left - 1:
        issues.append(f"escapes main-content left (left={rect.left:.1f} < main.left={main.left:.1f})")
    if rect.right > vw + 1:
        issues.append(f"overflows viewport (right={rect.right:.1f} > vw={vw})")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default="http://localhost:8000/?_t=views")
    parser.add_argument('--out-dir', default='exports')
    parser.add_argument('--timeout-ms', type=int, default=30000)
    args = parser.parse_args()

    url = args.url
    viewport: Viewport = {"width": 1440, "height": 900}

    out_dir = args.out_dir
    timeout_ms = args.timeout_ms

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=viewport)
        page.goto(url, timeout=timeout_ms)
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
        page.wait_for_timeout(1500)

        # Discover views from sidebar nav
        views: List[str] = page.evaluate(
            """
() => {
    const navs = Array.from(document.querySelectorAll('.nav-item[data-view]'));
    const names = navs
        .map(el => el.getAttribute('data-view'))
        .filter(Boolean);
    return Array.from(new Set(names));
}
"""
        )

        if not views:
            raise SystemExit('No views discovered (no .nav-item[data-view] found)')

        results: List[Tuple[str, str, List[str]]] = []

        for view in views:
            # Switch view via app code if available
            switched = page.evaluate(
                """
(viewName) => {
    try {
        if (typeof App !== 'undefined' && App.ui && typeof App.ui.switchView === 'function') {
            App.ui.switchView(viewName);
            return true;
        }
    } catch (e) {}
    return false;
}
""",
                view,
            )
            if not switched:
                results.append((view, '__view__', ['cannot switch view (App.ui.switchView not available)']))
                continue

            page.wait_for_timeout(1200)

            info = page.evaluate(
                """
(payload) => {
    const viewName = payload.viewName;

    const rect = (el) => {
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {left:r.left, right:r.right, top:r.top, bottom:r.bottom, width:r.width, height:r.height};
    };

    const styleInfo = (el) => {
        if (!el) return null;
        const cs = window.getComputedStyle(el);
        return {
            display: cs.display,
            visibility: cs.visibility,
            position: cs.position,
            left: cs.left,
            width: cs.width,
            height: cs.height,
            transform: cs.transform,
        };
    };

    const sidebar = rect(document.querySelector('#sidebar'));
    const main = rect(document.querySelector('#main-content'));

    const viewEl = document.getElementById(`view-${viewName}`);
    const viewRect = rect(viewEl);
    const viewStyle = styleInfo(viewEl);
    const viewClass = viewEl ? viewEl.className : null;

    // Collect chart-like elements inside current view
    const scope = viewEl || document;
    const nodes = Array.from(scope.querySelectorAll('[id^="chart-"] , canvas'));

    const items = nodes.map(el => {
        const panelEl = el.closest('.glass-panel');
        const containerEl = el.closest('.chart-container, .chart-container-sm, .chart-container-lg');
        const id = el.id ? `#${el.id}` : (el.tagName ? el.tagName.toLowerCase() : 'element');
        return {
            sel: id,
            rect: rect(el),
            container: rect(containerEl),
            panel: rect(panelEl),
            elStyle: styleInfo(el),
            panelStyle: styleInfo(panelEl),
            containerStyle: styleInfo(containerEl),
            inMain: !!(el && el.closest('#main-content')),
        };
    });

    return { viewport: {w: window.innerWidth, h: window.innerHeight}, sidebar, main, viewRect, viewStyle, viewClass, items };
}
""",
                {"viewName": view},
            )

            vw = int(info["viewport"]["w"])
            sidebar = _as_rect(info.get("sidebar"))
            main_rect = _as_rect(info.get("main"))

            for item in info.get("items", []):
                sel = item.get("sel")
                used = _as_rect(item.get("panel")) or _as_rect(item.get("container")) or _as_rect(item.get("rect"))
                if not used:
                    results.append((view, sel, ["missing"]))
                    continue

                # Skip hidden/zero-size elements to avoid noise
                if used.width <= 1 or used.height <= 1:
                    continue

                issues = _check_overlap(sidebar, main_rect, used, vw)
                if not item.get("inMain"):
                    issues.append("not inside #main-content (DOM nesting issue)")

                results.append((view, sel, issues))

            page.screenshot(path=f"{out_dir}/ui_{view}_1440x900.png", full_page=True)

        browser.close()

    print("view checks:")
    fail_count = 0
    for view, sel, issues in results:
        if issues:
            fail_count += 1
            print(f"- {view} {sel}: " + "; ".join(issues))
        else:
            print(f"- {view} {sel}: OK")

    if fail_count:
        raise SystemExit(f"FAIL: {fail_count} issues")


if __name__ == "__main__":
    main()

"""take_screenshot.py

Captura de pantalla de una URL usando Playwright.

Uso:
    python take_screenshot.py --url "http://localhost:5000/?_t=1" --out "exports/ui_dashboard_5000.png"
"""

from playwright.sync_api import sync_playwright
import argparse
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://localhost:8000', help='URL a capturar')
    parser.add_argument('--out', default='screenshot_full.png', help='Ruta de salida para la captura full page')
    parser.add_argument('--width', type=int, default=1920)
    parser.add_argument('--height', type=int, default=1080)
    parser.add_argument('--timeout', type=int, default=20000, help='Timeout (ms)')
    return parser.parse_args()

args = parse_args()

print(f"Tomando captura de pantalla... {args.url}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': args.width, 'height': args.height})

    try:
        page.goto(args.url, timeout=args.timeout)
        page.wait_for_load_state('networkidle', timeout=args.timeout)

        # Captura completa
        page.screenshot(path=args.out, full_page=True)
        print(f"✓ Captura completa guardada: {args.out}")

        # Captura opcional de una sección si existe
        sync_section = page.locator('text=社員台帳同期').locator('..')
        if sync_section.count() > 0:
            section_out = args.out.replace('.png', '_sync_section.png')
            sync_section.screenshot(path=section_out)
            print(f"✓ Sección de sincronización guardada: {section_out}")

        browser.close()
        print("\nCapturas guardadas exitosamente")

    except Exception as e:
        print(f"❌ Error: {e}")
        browser.close()

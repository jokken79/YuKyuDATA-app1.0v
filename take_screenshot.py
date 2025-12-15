"""
Captura de pantalla de la página web
"""
from playwright.sync_api import sync_playwright
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("Tomando captura de pantalla...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    try:
        page.goto('http://localhost:8000', timeout=10000)
        page.wait_for_load_state('networkidle', timeout=10000)

        # Captura completa
        page.screenshot(path='screenshot_full.png', full_page=True)
        print("✓ Captura completa guardada: screenshot_full.png")

        # Captura solo de la sección de sincronización
        sync_section = page.locator('text=社員台帳同期').locator('..')
        if sync_section.count() > 0:
            sync_section.screenshot(path='screenshot_sync_section.png')
            print("✓ Sección de sincronización guardada: screenshot_sync_section.png")

        browser.close()
        print("\n🎉 Capturas guardadas exitosamente")

    except Exception as e:
        print(f"❌ Error: {e}")
        browser.close()

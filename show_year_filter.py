"""
Muestra dónde está el filtro de años
"""
from playwright.sync_api import sync_playwright
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={'width': 1920, 'height': 1400})

    page.goto('http://localhost:8000')
    page.wait_for_load_state('networkidle')

    print("1. Sincronizando vacaciones para que aparezca el filtro de años...")
    page.locator('button:has-text("自動同期")').click()
    time.sleep(6)

    print("2. Buscando botones de año...")
    year_section = page.locator('#yearFilterSection')

    if year_section.is_visible():
        print("   ✓ Sección de filtro de años VISIBLE")

        # Tomar captura del área de filtro
        year_section.screenshot(path='year_filter_section.png')
        print("   ✓ Captura guardada: year_filter_section.png")
    else:
        print("   ✗ Sección de filtro de años NO visible")

    print("\n3. Captura completa del dashboard...")
    page.screenshot(path='dashboard_complete.png', full_page=True)
    print("   ✓ Captura guardada: dashboard_complete.png")

    time.sleep(2)
    browser.close()

print("\n✓ Listo - Revisa las capturas de pantalla")

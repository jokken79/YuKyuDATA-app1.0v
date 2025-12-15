"""
Captura simple después de sincronizar
"""
from playwright.sync_api import sync_playwright
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={'width': 1920, 'height': 1200})

    page.goto('http://localhost:8000')
    page.wait_for_load_state('networkidle')

    print("Sincronizando Genzai...")
    page.locator('button:has-text("派遣社員")').first.click()
    time.sleep(6)

    print("Sincronizando Ukeoi...")
    page.locator('button:has-text("請負社員")').first.click()
    time.sleep(6)

    print("Tomando captura...")
    page.screenshot(path='screenshot_with_active_counts.png', full_page=True)

    print("✓ Captura guardada: screenshot_with_active_counts.png")

    time.sleep(2)
    browser.close()

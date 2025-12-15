"""
Verifica el estado actual del dashboard
"""
from playwright.sync_api import sync_playwright
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    page.goto('http://localhost:8888')
    page.wait_for_load_state('networkidle')

    print('Pagina cargada en http://localhost:8888')

    # Verificar si existe la sección de leave requests
    leave_section = page.locator('#leaveRequestSection')
    if leave_section.count() > 0:
        is_visible = leave_section.is_visible()
        print(f'Seccion de solicitudes existe: SI')
        print(f'Seccion de solicitudes visible: {"SI" if is_visible else "NO (oculta)"}')
    else:
        print('Seccion de solicitudes existe: NO')

    # Tomar captura
    page.screenshot(path='dashboard_current.png', full_page=True)
    print('Captura guardada: dashboard_current.png')

    time.sleep(3)
    browser.close()

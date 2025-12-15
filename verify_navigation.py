"""
Verifica que el botón de navegación funciona correctamente
"""
from playwright.sync_api import sync_playwright
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    print("1. Cargando dashboard en http://localhost:8888...")
    page.goto('http://localhost:8888')
    page.wait_for_load_state('networkidle')
    print("   ✓ Página cargada")

    # Verificar que existe el botón de navegación
    print("\n2. Verificando botón de navegación 📝...")
    leave_btn = page.locator('#leaveRequestBtn')

    if leave_btn.count() > 0:
        print("   ✓ Botón 📝 (有給申請管理) encontrado")

        # Verificar estado inicial - sección debe estar oculta
        leave_section = page.locator('#leaveRequestSection')
        initial_visible = leave_section.is_visible()
        print(f"   • Estado inicial de sección: {'VISIBLE' if initial_visible else 'OCULTA'}")

        # Hacer clic en el botón
        print("\n3. Haciendo clic en el botón 📝...")
        leave_btn.click()
        time.sleep(1)

        # Verificar que la sección ahora está visible
        now_visible = leave_section.is_visible()
        print(f"   • Estado después del clic: {'VISIBLE ✓' if now_visible else 'OCULTA ✗'}")

        if now_visible:
            print("\n4. ✓ ¡ÉXITO! La sección de solicitudes ahora es accesible")

            # Verificar elementos visibles
            search_btn = page.locator('button:has-text("従業員を検索")')
            if search_btn.is_visible():
                print("   ✓ Botón de búsqueda de empleados visible")

            pending_table = page.locator('#pendingRequestsBody')
            if pending_table.count() > 0:
                print("   ✓ Tabla de solicitudes pendientes visible")

            # Captura de pantalla
            page.screenshot(path='leave_section_visible.png', full_page=True)
            print("\n   📸 Captura guardada: leave_section_visible.png")

            # Probar volver al dashboard
            print("\n5. Probando volver al dashboard...")
            leave_btn.click()
            time.sleep(1)

            dashboard = page.locator('#dashboard')
            if dashboard.is_visible():
                print("   ✓ Dashboard visible nuevamente")

            leave_hidden = not leave_section.is_visible()
            if leave_hidden:
                print("   ✓ Sección de solicitudes oculta correctamente")
        else:
            print("\n4. ✗ ERROR: La sección sigue oculta después del clic")
    else:
        print("   ✗ ERROR: Botón de navegación NO encontrado")

    time.sleep(2)
    browser.close()

print("\n" + "="*60)
print("VERIFICACIÓN COMPLETADA")
print("="*60)

"""
Prueba funcionalidad de filtro de empleados activos (在職中)
"""
from playwright.sync_api import sync_playwright
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("PRUEBA DE FUNCIONALIDAD 在職中 (EMPLEADOS ACTIVOS)")
print("=" * 70)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={'width': 1920, 'height': 1200})

    try:
        print("\n1. Cargando página...")
        page.goto('http://localhost:8000', timeout=10000)
        page.wait_for_load_state('networkidle')
        print("   ✓ Página cargada")

        # Capturar alertas
        alerts = []
        page.on("dialog", lambda dialog: (alerts.append(dialog.message()), dialog.accept()))

        print("\n2. Sincronizando Genzai...")
        page.locator('button:has-text("派遣社員")').first.click()
        time.sleep(5)

        genzai_total = page.locator('#genzaiCount').text_content()
        genzai_active = page.locator('#genzaiActiveCount').text_content()
        print(f"   Total: {genzai_total}")
        print(f"   在職中: {genzai_active}")

        print("\n3. Sincronizando Ukeoi...")
        page.locator('button:has-text("請負社員")').first.click()
        time.sleep(5)

        ukeoi_total = page.locator('#ukeoiCount').text_content()
        ukeoi_active = page.locator('#ukeoiActiveCount').text_content()
        print(f"   Total: {ukeoi_total}")
        print(f"   在職中: {ukeoi_active}")

        print("\n4. Click en '在職中のみ表示 (派遣)'...")
        page.locator('button:has-text("在職中のみ表示 (派遣)")').click()
        time.sleep(3)

        if len(alerts) > 0:
            print(f"   Alerta mostrada: {alerts[-1]}")

        print("\n5. Click en '在職中のみ表示 (請負)'...")
        page.locator('button:has-text("在職中のみ表示 (請負)")').click()
        time.sleep(3)

        if len(alerts) > 1:
            print(f"   Alerta mostrada: {alerts[-1]}")

        print("\n6. Captura final...")
        page.screenshot(path='screenshot_active_feature.png', full_page=True)
        print("   ✓ Guardada: screenshot_active_feature.png")

        print("\n" + "=" * 70)
        print("RESUMEN:")
        print("=" * 70)
        print(f"Genzai:  Total={genzai_total} | 在職中={genzai_active}")
        print(f"Ukeoi:   Total={ukeoi_total} | 在職中={ukeoi_active}")

        if genzai_active != "0" and ukeoi_active != "0":
            print("\n✅ ¡CONTADORES DE ACTIVOS FUNCIONAN!")
        else:
            print("\n❌ Contadores de activos en 0")

        print("=" * 70)

        time.sleep(2)
        browser.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        browser.close()

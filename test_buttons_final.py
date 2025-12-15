"""
Prueba final de botones con servidor nuevo
"""
from playwright.sync_api import sync_playwright
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("PRUEBA FINAL DE BOTONES")
print("=" * 60)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    try:
        print("\n1. Cargando página...")
        page.goto('http://localhost:8000', timeout=10000)
        page.wait_for_load_state('networkidle')
        print("   ✓ Página cargada")

        # Capturar mensajes
        messages = []
        page.on("console", lambda msg: messages.append(f"[{msg.type}] {msg.text}"))

        print("\n2. Estado ANTES de sincronizar:")
        genzai_before = page.locator('#genzaiCount').text_content()
        ukeoi_before = page.locator('#ukeoiCount').text_content()
        print(f"   派遣社員数: {genzai_before}")
        print(f"   請負社員数: {ukeoi_before}")

        print("\n3. Click en botón 🏢 派遣社員...")
        page.locator('button:has-text("派遣社員")').click()

        # Esperar notificación
        print("   Esperando notificación...")
        time.sleep(4)

        print("\n4. Estado DESPUÉS de sincronizar Genzai:")
        genzai_after = page.locator('#genzaiCount').text_content()
        print(f"   派遣社員数: {genzai_after}")

        if genzai_after != genzai_before:
            print(f"   ✓ ¡CAMBIÓ! {genzai_before} → {genzai_after}")
        else:
            print(f"   ✗ NO CAMBIÓ (sigue en {genzai_after})")

        print("\n5. Click en botón 📋 請負社員...")
        page.locator('button:has-text("請負社員")').click()

        print("   Esperando notificación...")
        time.sleep(4)

        print("\n6. Estado DESPUÉS de sincronizar Ukeoi:")
        ukeoi_after = page.locator('#ukeoiCount').text_content()
        print(f"   請負社員数: {ukeoi_after}")

        if ukeoi_after != ukeoi_before:
            print(f"   ✓ ¡CAMBIÓ! {ukeoi_before} → {ukeoi_after}")
        else:
            print(f"   ✗ NO CAMBIÓ (sigue en {ukeoi_after})")

        print("\n7. Mensajes relevantes:")
        for msg in messages:
            if 'sync' in msg.lower() or 'error' in msg.lower() or '成功' in msg or '失敗' in msg:
                print(f"   {msg}")

        print("\n8. Captura final...")
        page.screenshot(path='screenshot_test_final.png', full_page=True)
        print("   ✓ Guardada: screenshot_test_final.png")

        print("\n" + "=" * 60)
        print("RESUMEN:")
        print("=" * 60)
        print(f"Genzai: {genzai_before} → {genzai_after}")
        print(f"Ukeoi:  {ukeoi_before} → {ukeoi_after}")

        if genzai_after != "0" and ukeoi_after != "0":
            print("\n✅ ¡BOTONES FUNCIONAN CORRECTAMENTE!")
        else:
            print("\n❌ Botones no actualizan contadores")

        print("=" * 60)

        time.sleep(2)
        browser.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        browser.close()

"""
Test de los botones de sincronización
"""
from playwright.sync_api import sync_playwright
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("Probando botones de sincronización...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Con interfaz visible
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    try:
        print("\n1. Navegando a http://localhost:8000...")
        page.goto('http://localhost:8000', timeout=10000)
        page.wait_for_load_state('networkidle', timeout=10000)
        print("   ✓ Página cargada")

        # Capturar errores de consola
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))

        # Capturar errores de red
        page.on("requestfailed", lambda request: print(f"   ❌ Request falló: {request.url} - {request.failure}"))

        print("\n2. Buscando botón 派遣社員...")
        genzai_button = page.locator('button:has-text("派遣社員")')
        if genzai_button.count() > 0:
            print(f"   ✓ Botón encontrado (count: {genzai_button.count()})")

            print("\n3. Haciendo clic en 派遣社員...")
            genzai_button.click()
            print("   ✓ Click ejecutado")

            # Esperar respuesta
            print("\n4. Esperando respuesta del servidor...")
            time.sleep(3)

            # Verificar contador
            genzai_count = page.locator('#genzaiCount').text_content()
            print(f"   Contador 派遣社員数: {genzai_count}")

        else:
            print("   ❌ Botón NO encontrado")

        print("\n5. Buscando botón 請負社員...")
        ukeoi_button = page.locator('button:has-text("請負社員")')
        if ukeoi_button.count() > 0:
            print(f"   ✓ Botón encontrado (count: {ukeoi_button.count()})")

            print("\n6. Haciendo clic en 請負社員...")
            ukeoi_button.click()
            print("   ✓ Click ejecutado")

            # Esperar respuesta
            print("\n7. Esperando respuesta del servidor...")
            time.sleep(3)

            # Verificar contador
            ukeoi_count = page.locator('#ukeoiCount').text_content()
            print(f"   Contador 請負社員数: {ukeoi_count}")

        else:
            print("   ❌ Botón NO encontrado")

        print("\n8. Mensajes de consola del navegador:")
        for msg in console_messages:
            print(f"   {msg}")

        print("\n9. Tomando captura final...")
        page.screenshot(path='screenshot_after_clicks.png')
        print("   ✓ Captura guardada: screenshot_after_clicks.png")

        time.sleep(2)
        browser.close()
        print("\n✓ Prueba completada")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        browser.close()

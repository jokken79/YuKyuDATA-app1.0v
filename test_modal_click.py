"""
Test clicking on employee in factory modal
"""
from playwright.sync_api import sync_playwright
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("="*60)
print("  TEST: Click on Employee in Factory Modal")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    print("\n1. Loading page...")
    page.goto('http://localhost:8888')
    page.wait_for_selector('.status-badge.connected', timeout=20000)
    print("   ✓ Page loaded and synced")

    time.sleep(2)

    print("\n2. Opening factory modal...")
    # Click on a factory card
    factory_cards = page.locator('.factory-card')
    if factory_cards.count() > 0:
        factory_cards.first.click()
        print("   ✓ Factory modal opened")
        time.sleep(1)

        # Verify list modal is visible
        list_modal = page.locator('#listModal.active')
        if list_modal.count() > 0:
            print("   ✓ List modal is active")

            print("\n3. Clicking on employee row...")
            # Click on first employee row
            employee_rows = page.locator('#listModal tbody tr')
            if employee_rows.count() > 0:
                employee_rows.first.click()
                print("   ✓ Clicked on employee")

                time.sleep(1)

                # Check if employee modal opened
                employee_modal = page.locator('#employeeModal')
                modal_display = page.evaluate('document.getElementById("employeeModal").style.display')

                if modal_display == 'flex':
                    print("   ✓ Employee modal opened successfully!")

                    # Verify employee data is displayed
                    employee_name = page.locator('#modalName').inner_text()
                    employee_num = page.locator('#modalEmpNum').inner_text()

                    print(f"\n   Employee Details:")
                    print(f"     Name: {employee_name}")
                    print(f"     Number: {employee_num}")

                    # Take screenshot
                    page.screenshot(path='employee_modal_test.png')
                    print("\n   📸 Screenshot saved: employee_modal_test.png")

                    print("\n   ✓✓✓ SUCCESS: Modal works correctly! ✓✓✓")
                else:
                    print("   ✗ ERROR: Employee modal did not open")
                    print(f"     Modal display: {modal_display}")

                time.sleep(2)
            else:
                print("   ✗ No employee rows found")
        else:
            print("   ✗ List modal did not activate")
    else:
        print("   ✗ No factory cards found")

    browser.close()

print("\n" + "="*60)
print("  TEST COMPLETED")
print("="*60)

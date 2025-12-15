"""
Test clicking employee in factory modal to verify it opens employee details
"""
from playwright.sync_api import sync_playwright
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("="*60)
print("  TEST: Click Employee in Factory Modal")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    print("\n1. Loading page...")
    page.goto('http://localhost:8000')

    # Wait for auto-sync
    try:
        page.wait_for_selector('.status-badge.connected', timeout=20000)
        print("   ✓ Page loaded and synced")
    except:
        print("   ⚠ Sync timeout")

    time.sleep(2)

    # Check if we're viewing a specific year
    try:
        year_buttons = page.locator('.year-filter-btn').all()
        if len(year_buttons) > 0:
            print(f"\n2. Found {len(year_buttons)} year filter buttons")
            # Click first year (usually latest)
            year_buttons[0].click()
            print(f"   ✓ Selected year filter")
            time.sleep(1)
    except Exception as e:
        print(f"   ℹ No year filter: {e}")

    print("\n3. Looking for factory chart...")
    # Scroll to factory section
    factory_section = page.locator('#factorySection')
    if factory_section.is_visible():
        factory_section.scroll_into_view_if_needed()
        print("   ✓ Factory section visible")
        time.sleep(1)

        # Click on first factory bar
        factory_bars = page.locator('#factoryChartContainer > div')
        if factory_bars.count() > 0:
            first_factory = factory_bars.first
            factory_name = first_factory.locator('div').first.inner_text()
            print(f"\n4. Clicking on factory: {factory_name}")
            first_factory.click()
            time.sleep(1)

            # Verify list modal opened
            list_modal = page.locator('#listModal')
            modal_display = page.evaluate('document.getElementById("listModal").style.display')

            if modal_display == 'flex':
                print("   ✓ Factory modal opened!")

                # Check modal title and count
                modal_title = page.locator('#listModalTitle').inner_text()
                modal_count = page.locator('#listModalCount').inner_text()
                print(f"   Title: {modal_title}")
                print(f"   Count: {modal_count}")

                # Try to click on first employee
                print("\n5. Clicking on first employee...")
                employee_rows = page.locator('#listModal tbody tr')
                if employee_rows.count() > 0:
                    # Get employee name before clicking
                    first_row = employee_rows.first
                    emp_name = first_row.locator('td').first.inner_text()
                    print(f"   Employee: {emp_name}")

                    # Click the row
                    first_row.click()
                    print("   ✓ Clicked on employee row")
                    time.sleep(1)

                    # Check if employee modal opened
                    emp_modal = page.locator('#employeeModal')
                    emp_modal_display = page.evaluate('document.getElementById("employeeModal").style.display')

                    if emp_modal_display == 'flex':
                        print("\n   ✓✓✓ SUCCESS: Employee modal opened!")

                        # Get employee details
                        modal_name = page.locator('#modalName').inner_text()
                        modal_num = page.locator('#modalEmpNum').inner_text()
                        modal_year = page.locator('#modalYear').inner_text()

                        print(f"\n   Employee Details:")
                        print(f"     Name: {modal_name}")
                        print(f"     Number: {modal_num}")
                        print(f"     Year: {modal_year}")

                        # Take screenshot
                        page.screenshot(path='employee_modal_opened.png')
                        print("\n   📸 Screenshot: employee_modal_opened.png")
                    else:
                        print(f"\n   ✗✗✗ FAILED: Employee modal did not open!")
                        print(f"   Modal display value: {emp_modal_display}")

                        # Check for JavaScript errors
                        errors = page.evaluate('''
                            window.jsErrors || []
                        ''')
                        print(f"   JavaScript errors: {errors}")

                        # Take screenshot of failure
                        page.screenshot(path='employee_modal_failed.png')
                        print("   📸 Screenshot: employee_modal_failed.png")
                else:
                    print("   ✗ No employee rows found")
            else:
                print(f"   ✗ Factory modal did not open (display: {modal_display})")
        else:
            print("   ✗ No factory bars found")
    else:
        print("   ✗ Factory section not visible")

    print("\n6. Waiting 3 seconds for observation...")
    time.sleep(3)

    browser.close()

print("\n" + "="*60)
print("  TEST COMPLETED")
print("="*60)

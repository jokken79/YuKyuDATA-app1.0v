"""
Comprehensive investigation of all data counts visible on the frontend
"""
from playwright.sync_api import sync_playwright
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("="*60)
print("  FRONTEND DATA COUNT INVESTIGATION")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    print("\n1. Loading page at http://localhost:8888...")
    page.goto('http://localhost:8888')

    # Wait for auto-sync to complete
    print("   ⏳ Waiting for automatic synchronization...")
    try:
        page.wait_for_selector('.status-badge.connected', timeout=20000)
        print("   ✓ Auto-sync completed")
    except:
        print("   ⚠ Sync timeout")

    time.sleep(2)

    print("\n2. Capturing ALL visible data counters:")
    print("   " + "-"*56)

    # Main data count
    try:
        data_count = page.locator('#dataCount').inner_text()
        print(f"   📊 Main Data Count (#dataCount): {data_count}")
    except:
        print(f"   ✗ #dataCount not found")

    # Total employees count (if different element exists)
    try:
        total_employees = page.locator('#totalEmployees').inner_text()
        print(f"   👥 Total Employees (#totalEmployees): {total_employees}")
    except:
        pass

    # Year selector options
    try:
        year_selector = page.locator('#yearSelect')
        year_options = year_selector.locator('option').all()
        print(f"\n   📅 Available Years: {len(year_options)} years")
        for option in year_options:
            year_text = option.inner_text()
            print(f"      - {year_text}")
    except:
        print(f"   ✗ Year selector not found")

    # Factory cards count
    try:
        factory_cards = page.locator('.factory-card').all()
        print(f"\n   🏭 Factory Cards: {len(factory_cards)} factories")

        # Click each factory and count employees
        total_rows_across_factories = 0
        for i, card in enumerate(factory_cards[:5]):  # Check first 5 factories
            factory_name = card.locator('.factory-name').inner_text()
            count_text = card.locator('.employee-count').inner_text()
            print(f"      - {factory_name}: {count_text}")

            # Click to see employee list
            card.click()
            time.sleep(0.5)

            # Count rows in list modal
            rows = page.locator('#listModal tbody tr').all()
            total_rows_across_factories += len(rows)
            print(f"        (Modal shows {len(rows)} employee rows)")

            # Close modal
            page.locator('#closeListModal').click()
            time.sleep(0.3)

        print(f"\n   📋 Total rows seen in first 5 factories: {total_rows_across_factories}")
    except Exception as e:
        print(f"   ✗ Factory cards error: {e}")

    # Check if there's a table with all data
    try:
        all_data_rows = page.locator('#dataSection table tbody tr').all()
        if len(all_data_rows) > 0:
            print(f"\n   📄 Data Table Rows: {len(all_data_rows)} rows")
    except:
        pass

    # Execute JavaScript to get AppState data
    print("\n3. JavaScript AppState Investigation:")
    try:
        app_state_length = page.evaluate('AppState.data ? AppState.data.length : 0')
        print(f"   📦 AppState.data.length: {app_state_length}")

        # Check if data has nested arrays or duplicates
        unique_ids = page.evaluate('''
            AppState.data ? new Set(AppState.data.map(d => d.id)).size : 0
        ''')
        print(f"   🔑 Unique IDs in AppState.data: {unique_ids}")

        # Sample of data structure
        sample_data = page.evaluate('''
            AppState.data ? AppState.data.slice(0, 3).map(d => ({
                id: d.id,
                name: d.name,
                year: d.year,
                employeeNum: d.employeeNum
            })) : []
        ''')
        print(f"\n   📋 Sample data (first 3 records):")
        for item in sample_data:
            print(f"      - {item}")

    except Exception as e:
        print(f"   ✗ AppState error: {e}")

    # Check all text elements that might show numbers
    print("\n4. Searching for ALL number displays on page:")
    try:
        # Get all text content and find numbers > 1000
        all_text = page.evaluate('''
            Array.from(document.querySelectorAll('*'))
                .map(el => el.textContent.trim())
                .filter(text => /\\b[1-9]\\d{3,}\\b/.test(text))
                .filter((v, i, a) => a.indexOf(v) === i)
        ''')
        print(f"   🔍 Numbers > 1000 found on page:")
        for text in all_text[:10]:  # Show first 10
            print(f"      - {text[:100]}")
    except Exception as e:
        print(f"   ✗ Number search error: {e}")

    # Take screenshot
    page.screenshot(path='frontend_counts_investigation.png', full_page=True)
    print(f"\n   📸 Screenshot saved: frontend_counts_investigation.png")

    print("\n5. Waiting 3 seconds for observation...")
    time.sleep(3)

    browser.close()

print("\n" + "="*60)
print("  INVESTIGATION COMPLETED")
print("="*60)

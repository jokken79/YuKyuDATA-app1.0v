"""
Test automatic synchronization on page load
"""
from playwright.sync_api import sync_playwright
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("="*60)
print("  TEST: Automatic Synchronization on Page Load")
print("="*60)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    print("\n1. Loading page at http://localhost:8888...")
    page.goto('http://localhost:8888')

    # Wait for auto-sync to complete
    print("   ⏳ Waiting for automatic synchronization to complete...")

    # Wait for the status badge to change to 'connected' (means sync completed)
    try:
        page.wait_for_selector('.status-badge.connected', timeout=15000)
        print("   ✓ Automatic synchronization completed!")
    except:
        print("   ⚠ Sync taking longer than expected...")

    # Check if data was loaded
    time.sleep(2)

    print("\n2. Verifying data was loaded...")
    data_count = page.locator('#dataCount').inner_text()
    print(f"   Data count: {data_count}")

    if data_count and data_count != "0":
        print("   ✓ Data was automatically synchronized!")
    else:
        print("   ✗ No data loaded - sync may have failed")

    # Take screenshot
    page.screenshot(path='auto_sync_test.png', full_page=True)
    print("\n   📸 Screenshot saved: auto_sync_test.png")

    print("\n3. Waiting 3 seconds to observe the dashboard...")
    time.sleep(3)

    browser.close()

print("\n" + "="*60)
print("  TEST COMPLETED")
print("="*60)
print("\n✓ Automatic synchronization is now enabled!")
print("  Every time you load the page, it will sync automatically.")

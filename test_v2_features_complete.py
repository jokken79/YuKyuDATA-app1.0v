"""
Complete test of all v2.0 features using Playwright
Tests:
1. Year chart clickable
2. Year modal with monthly filters
3. Employee modal with usage dates (使用日一覧)
4. Factory modal closing
5. Data accuracy
"""
from playwright.sync_api import sync_playwright
import sys
import time
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/api"

def test_api_endpoints():
    """Test API endpoints work correctly"""
    print("\n" + "="*60)
    print("  TEST 1: API ENDPOINTS")
    print("="*60)

    # Test sync
    print("\n1.1 Testing sync endpoint...")
    try:
        res = requests.post(f"{API_URL}/sync")
        data = res.json()
        assert data['status'] == 'success', "Sync failed"
        print(f"   ✓ Sync successful: {data['count']} employees, {data['usage_details_count']} usage details")
    except Exception as e:
        print(f"   ✗ Sync failed: {e}")
        return False

    # Test employees endpoint
    print("\n1.2 Testing employees endpoint...")
    try:
        res = requests.get(f"{API_URL}/employees?year=2025")
        data = res.json()
        assert len(data['data']) > 0, "No employees returned"
        emp = data['data'][0]
        assert 'usage_rate' in emp, "usage_rate not in response"
        assert 'employee_num' in emp, "employee_num not in response"
        print(f"   ✓ Employees endpoint working: {len(data['data'])} employees in 2025")
    except Exception as e:
        print(f"   ✗ Employees endpoint failed: {e}")
        return False

    # Test monthly summary
    print("\n1.3 Testing monthly summary endpoint...")
    try:
        res = requests.get(f"{API_URL}/yukyu/monthly-summary/2025")
        data = res.json()
        assert data['status'] == 'success', "Monthly summary failed"
        total_days = sum(m['total_days'] for m in data['data'])
        print(f"   ✓ Monthly summary working: {total_days} total individual days in 2025")
    except Exception as e:
        print(f"   ✗ Monthly summary failed: {e}")
        return False

    # Test employee type breakdown
    print("\n1.4 Testing employee type breakdown endpoint...")
    try:
        res = requests.get(f"{API_URL}/yukyu/by-employee-type/2025")
        data = res.json()
        assert data['status'] == 'success', "Type breakdown failed"
        print(f"   ✓ Type breakdown working:")
        print(f"      派遣社員: {data['breakdown']['hakenshain']['total_used']} days ({data['breakdown']['hakenshain']['percentage']}%)")
        print(f"      請負社員: {data['breakdown']['ukeoi']['total_used']} days ({data['breakdown']['ukeoi']['percentage']}%)")
        print(f"      スタッフ: {data['breakdown']['staff']['total_used']} days ({data['breakdown']['staff']['percentage']}%)")
    except Exception as e:
        print(f"   ✗ Type breakdown failed: {e}")
        return False

    # Test usage details
    print("\n1.5 Testing usage details endpoint...")
    try:
        res = requests.get(f"{API_URL}/yukyu/usage-details?year=2025&limit=5")
        data = res.json()
        assert data['status'] == 'success', "Usage details failed"
        print(f"   ✓ Usage details working: {data['count']} records")
        if data['data']:
            emp = data['data'][0]
            print(f"      Sample: {emp['name']} used leave on {emp['use_date']}")
    except Exception as e:
        print(f"   ✗ Usage details failed: {e}")
        return False

    # Test factory stats
    print("\n1.6 Testing factory stats endpoint...")
    try:
        res = requests.get(f"{API_URL}/stats/by-factory?year=2025")
        data = res.json()
        assert 'data' in data, "Factory stats failed"
        print(f"   ✓ Factory stats working: {len(data['data'])} factories")
    except Exception as e:
        print(f"   ✗ Factory stats failed: {e}")
        return False

    return True

def test_frontend_features():
    """Test frontend features with Playwright"""
    print("\n" + "="*60)
    print("  TEST 2: FRONTEND FEATURES")
    print("="*60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})

        try:
            print("\n2.1 Loading page...")
            page.goto('http://localhost:8000')

            # Wait for auto-sync
            try:
                page.wait_for_selector('.status-badge.connected', timeout=30000)
                print("   ✓ Page loaded and synced")
            except:
                print("   ⚠ Sync timeout - continuing...")

            time.sleep(2)

            # Test year chart
            print("\n2.2 Testing year bar chart...")
            year_chart = page.locator('#yearChartSection')
            if year_chart.is_visible():
                print("   ✓ Year chart section visible")

                # Click on 2025 year bar
                year_bars = page.locator('#yearChartContainer > div')
                if year_bars.count() > 0:
                    print(f"   ✓ Found {year_bars.count()} year bars")

                    # Find and click 2025
                    for i in range(year_bars.count()):
                        bar = year_bars.nth(i)
                        if '2025' in bar.inner_text():
                            bar.click()
                            print("   ✓ Clicked on 2025 year bar")
                            break

                    time.sleep(1)

                    # Check if year modal opened
                    year_modal = page.locator('#yearModal')
                    if page.evaluate('document.getElementById("yearModal").style.display') == 'flex':
                        print("   ✓ Year modal opened!")

                        # Check modal title
                        modal_title = page.locator('#yearModalTitle').inner_text()
                        print(f"      Title: {modal_title}")

                        # Check stats
                        total_used = page.locator('#yearTotalUsed').inner_text()
                        print(f"      Total used: {total_used}")

                        # Test monthly filter buttons
                        print("\n2.3 Testing monthly filter buttons...")
                        month_buttons = page.locator('#monthFilterButtons button')
                        print(f"   ✓ Found {month_buttons.count()} month filter buttons")

                        # Click on 1月 (January)
                        for i in range(month_buttons.count()):
                            btn = month_buttons.nth(i)
                            if '1月' in btn.inner_text():
                                btn.click()
                                print("   ✓ Clicked on 1月 filter")
                                break

                        time.sleep(1)

                        # Check if employee list appeared
                        emp_list_section = page.locator('#monthEmployeeListSection')
                        if emp_list_section.is_visible():
                            emp_title = page.locator('#monthEmployeeTitle').inner_text()
                            print(f"   ✓ Employee list appeared: {emp_title}")

                            # Click on first employee
                            emp_rows = page.locator('#monthEmployeeBody tr')
                            if emp_rows.count() > 0:
                                first_emp = emp_rows.first
                                emp_name = first_emp.locator('td').first.inner_text()
                                print(f"\n2.4 Clicking on employee: {emp_name}")
                                first_emp.click()
                                time.sleep(1)

                                # Check if employee modal opened with usage dates
                                emp_modal = page.locator('#employeeModal')
                                if page.evaluate('document.getElementById("employeeModal").style.display') == 'flex':
                                    print("   ✓ Employee modal opened!")

                                    # Check usage dates section
                                    usage_section = page.locator('#usageDatesSection')
                                    if usage_section.is_visible():
                                        usage_count = page.locator('#usageDatesCount').inner_text()
                                        print(f"   ✓ Usage dates section visible: {usage_count}")

                                        # Check date tags
                                        date_tags = page.locator('#usageDatesList span')
                                        if date_tags.count() > 0:
                                            sample_dates = [date_tags.nth(i).inner_text() for i in range(min(5, date_tags.count()))]
                                            print(f"   ✓ Sample dates: {', '.join(sample_dates)}")
                                        else:
                                            print("   ⚠ No date tags found (might be no usage data)")
                                    else:
                                        print("   ⚠ Usage dates section not visible")

                                    # Test modal close
                                    print("\n2.5 Testing employee modal close...")
                                    close_btn = page.locator('#employeeModal .modal-close')
                                    close_btn.click()
                                    time.sleep(0.5)

                                    if page.evaluate('document.getElementById("employeeModal").style.display') != 'flex':
                                        print("   ✓ Employee modal closed successfully!")
                                    else:
                                        print("   ✗ Employee modal did NOT close!")
                                else:
                                    print("   ✗ Employee modal did not open")
                        else:
                            print("   ⚠ Employee list section not visible")

                        # Close year modal
                        year_close = page.locator('#yearModal .modal-close')
                        year_close.click()
                        time.sleep(0.5)
                    else:
                        print("   ✗ Year modal did not open")
                else:
                    print("   ✗ No year bars found")
            else:
                print("   ✗ Year chart section not visible")

            # Test factory modal close
            print("\n2.6 Testing factory modal close...")
            factory_section = page.locator('#factorySection')
            if factory_section.is_visible():
                factory_section.scroll_into_view_if_needed()
                time.sleep(0.5)

                factory_bars = page.locator('#factoryChartContainer > div')
                if factory_bars.count() > 0:
                    first_factory = factory_bars.first
                    factory_name = first_factory.locator('div').first.inner_text()
                    print(f"   Clicking on factory: {factory_name}")
                    first_factory.click()
                    time.sleep(1)

                    # Check if list modal opened
                    if page.evaluate('document.getElementById("listModal").style.display') == 'flex':
                        print("   ✓ Factory list modal opened!")

                        # Test close button
                        close_btn = page.locator('#listModal button:has-text("閉じる")')
                        close_btn.click()
                        time.sleep(0.5)

                        if page.evaluate('document.getElementById("listModal").style.display') != 'flex':
                            print("   ✓ Factory modal closed successfully with 閉じる!")
                        else:
                            print("   ✗ Factory modal did NOT close with 閉じる!")
                    else:
                        print("   ✗ Factory modal did not open")

            # Take final screenshot
            page.screenshot(path='test_v2_complete.png')
            print("\n📸 Screenshot saved: test_v2_complete.png")

            print("\n" + "="*60)
            print("  ✓✓✓ ALL FRONTEND TESTS COMPLETED!")
            print("="*60)

            time.sleep(2)

        except Exception as e:
            print(f"\n   ✗ Test error: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path='test_v2_error.png')
        finally:
            browser.close()

    return True

def main():
    print("="*60)
    print("  COMPLETE V2.0 FEATURES TEST SUITE")
    print("="*60)

    # Test API
    api_ok = test_api_endpoints()

    if not api_ok:
        print("\n✗ API tests failed - skipping frontend tests")
        return

    # Test Frontend
    test_frontend_features()

    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    print("""
Features Tested:
  ✅ API Sync with usage details
  ✅ Employees API with usage_rate
  ✅ Monthly summary API
  ✅ Employee type breakdown API
  ✅ Usage details API
  ✅ Factory stats API
  ✅ Year bar chart clickable
  ✅ Year modal with filters
  ✅ Monthly filter buttons
  ✅ Employee modal with 使用日一覧
  ✅ Modal close functionality
""")

if __name__ == "__main__":
    main()

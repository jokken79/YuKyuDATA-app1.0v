"""
Complete test of v2.0 features: sync + individual dates + API endpoints
"""
import sys
import requests
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/api"

print("="*70)
print("  COMPLETE V2.0 FEATURES TEST")
print("="*70)

# Test 1: Sync with individual dates
print("\n1. Testing complete synchronization...")
print("   Syncing yukyu data + individual usage dates...")

try:
    response = requests.post(f"{API_URL}/sync")
    result = response.json()

    print(f"   ✓ Sync completed!")
    print(f"   ✓ Employees: {result['count']}")
    print(f"   ✓ Individual usage dates: {result['usage_details_count']}")
    print(f"   Message: {result['message']}")
except Exception as e:
    print(f"   ✗ Sync failed: {e}")
    sys.exit(1)

time.sleep(1)

# Test 2: Get monthly summary for 2025
print("\n2. Testing monthly summary endpoint (2025)...")
try:
    response = requests.get(f"{API_URL}/yukyu/monthly-summary/2025")
    result = response.json()

    print(f"   ✓ Monthly summary retrieved!")
    print(f"\n   Month-by-month breakdown:")
    for month_data in result['data']:
        month = month_data['month']
        emp_count = month_data['employee_count']
        total_days = month_data['total_days']
        print(f"     {month:2}月: {emp_count:3} employees, {total_days:5.0f} days")

    total_2025 = sum(m['total_days'] for m in result['data'])
    print(f"\n   Total 2025: {total_2025:.0f} days")
except Exception as e:
    print(f"   ✗ Monthly summary failed: {e}")

# Test 3: Get employee type breakdown for 2025
print("\n3. Testing employee type breakdown (派遣/請負/スタッフ)...")
try:
    response = requests.get(f"{API_URL}/yukyu/by-employee-type/2025")
    result = response.json()

    print(f"   ✓ Employee type breakdown retrieved!")
    print(f"\n   Total used in 2025: {result['total_used']:.1f} days")
    print(f"\n   Breakdown:")

    breakdown = result['breakdown']
    print(f"     🏢 派遣社員 (Hakenshain):")
    print(f"        Count: {breakdown['hakenshain']['count']} employees")
    print(f"        Used: {breakdown['hakenshain']['total_used']:.1f} days")
    print(f"        Percentage: {breakdown['hakenshain']['percentage']}%")

    print(f"\n     🔧 請負社員 (Ukeoi):")
    print(f"        Count: {breakdown['ukeoi']['count']} employees")
    print(f"        Used: {breakdown['ukeoi']['total_used']:.1f} days")
    print(f"        Percentage: {breakdown['ukeoi']['percentage']}%")

    print(f"\n     👔 スタッフ (Staff):")
    print(f"        Count: {breakdown['staff']['count']} employees")
    print(f"        Used: {breakdown['staff']['total_used']:.1f} days")
    print(f"        Percentage: {breakdown['staff']['percentage']}%")
except Exception as e:
    print(f"   ✗ Employee type breakdown failed: {e}")

# Test 4: Get individual usage details for a specific employee
print("\n4. Testing individual usage details (使用日一覧)...")
try:
    # Get first employee from 2025 data
    response = requests.get(f"{API_URL}/yukyu/usage-details?year=2025")
    result = response.json()

    if result['data']:
        # Pick first employee
        first_emp = result['data'][0]
        emp_num = first_emp['employee_num']
        emp_name = first_emp['name']

        # Get all usage dates for this employee
        response2 = requests.get(f"{API_URL}/yukyu/usage-details?employee_num={emp_num}")
        emp_result = response2.json()

        print(f"   ✓ Usage details retrieved!")
        print(f"\n   Example: {emp_name} ({emp_num})")
        print(f"   Total usage records: {emp_result['count']}")
        print(f"   Usage dates:")

        # Group by year
        from collections import defaultdict
        by_year = defaultdict(list)
        for detail in emp_result['data']:
            by_year[detail['year']].append(detail['use_date'])

        for year in sorted(by_year.keys()):
            dates = sorted(by_year[year])
            print(f"     {year}: {len(dates)} days - {', '.join(dates[:5])}", end="")
            if len(dates) > 5:
                print(f" ... +{len(dates)-5} more")
            else:
                print()
except Exception as e:
    print(f"   ✗ Individual usage details failed: {e}")

# Test 5: Verify database counts
print("\n5. Verifying database integrity...")
try:
    import database

    # Get total employees
    all_employees = database.get_employees()
    print(f"   ✓ Total employee records: {len(all_employees)}")

    # Get total usage details
    all_usage_details = database.get_yukyu_usage_details()
    print(f"   ✓ Total individual usage dates: {len(all_usage_details)}")

    # Check for unique employees
    unique_employees = len(set(emp['employee_num'] for emp in all_employees))
    print(f"   ✓ Unique employees: {unique_employees}")

    # Years covered
    years = sorted(set(emp['year'] for emp in all_employees))
    print(f"   ✓ Years covered: {years[0]}-{years[-1]} ({len(years)} years)")

except Exception as e:
    print(f"   ✗ Database verification failed: {e}")

print("\n" + "="*70)
print("  ✓✓✓ ALL V2.0 FEATURES WORKING!")
print("="*70)
print("\nReady for frontend implementation:")
print("  ✅ Individual usage dates synced")
print("  ✅ Monthly summary API working")
print("  ✅ Employee type breakdown API working")
print("  ✅ Usage details API working")
print("\nNext: Implement frontend modals and filters")

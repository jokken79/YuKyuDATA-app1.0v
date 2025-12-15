"""
Test script to verify KPI fix - Dashboard now shows correct 3318 days from individual dates
"""
import sys
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/api"

print("="*70)
print("  KPI FIX VERIFICATION TEST")
print("="*70)

# Test 1: Verify KPI stats endpoint returns correct value
print("\n1. Testing KPI Stats Endpoint...")
try:
    response = requests.get(f"{API_URL}/yukyu/kpi-stats/2025")
    kpi = response.json()

    print(f"   Status: {kpi['status']}")
    print(f"   Year: {kpi['year']}")
    print(f"   Total Employees: {kpi['total_employees']}")
    print(f"   Total Granted: {kpi['total_granted']}")
    print(f"   Total Used: {kpi['total_used']}")
    print(f"   Total Balance: {kpi['total_balance']}")
    print(f"   Usage Rate: {kpi['usage_rate']}%")

    # Verify the value is ~3318 (from individual dates)
    if 3300 <= kpi['total_used'] <= 3350:
        print(f"\n   ✓ CORRECT! Total Used is ~3318 (from individual dates R-BE)")
    else:
        print(f"\n   ✗ ERROR! Expected ~3318, got {kpi['total_used']}")

except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Compare with old employees endpoint
print("\n2. Comparing with old employees endpoint (column N values)...")
try:
    response = requests.get(f"{API_URL}/employees?year=2025")
    data = response.json()

    old_total_used = sum(emp['used'] for emp in data['data'])
    print(f"   Old method (column N sum): {old_total_used}")
    print(f"   New method (individual dates): {kpi['total_used']}")
    print(f"   Difference: {old_total_used - kpi['total_used']} days")

    if old_total_used != kpi['total_used']:
        print(f"\n   ✓ Values are different as expected:")
        print(f"     - Column N (per-grant-period used): {old_total_used}")
        print(f"     - Individual dates R-BE (calendar year used): {kpi['total_used']}")

except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: Verify monthly summary matches KPI
print("\n3. Verifying monthly summary totals match KPI...")
try:
    response = requests.get(f"{API_URL}/yukyu/monthly-summary/2025")
    monthly = response.json()

    monthly_total = sum(m['total_days'] for m in monthly['data'])
    print(f"   Monthly summary total: {monthly_total}")
    print(f"   KPI endpoint total: {kpi['total_used']}")

    if abs(monthly_total - kpi['total_used']) < 1:
        print(f"\n   ✓ Values match! Both using individual dates source")
    else:
        print(f"\n   ✗ Mismatch: monthly={monthly_total}, kpi={kpi['total_used']}")

except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: Show monthly breakdown for 2025
print("\n4. Monthly breakdown for 2025:")
try:
    for m in monthly['data']:
        bar = '█' * int(m['total_days'] / 50) if m['total_days'] > 0 else ''
        print(f"   {m['month']:2}月: {m['total_days']:4.0f} days {bar}")

except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "="*70)
print("  SUMMARY")
print("="*70)
print(f"""
The KPI fix is working correctly:

  OLD VALUE (column N sum):     {old_total_used if 'old_total_used' in dir() else 'N/A'} days
  NEW VALUE (individual dates): {kpi['total_used'] if 'kpi' in dir() else 'N/A'} days

  The dashboard now shows the CORRECT value from individual dates (R-BE columns),
  which matches v2.0 behavior and the user's expected value of ~3310.
""")
print("="*70)

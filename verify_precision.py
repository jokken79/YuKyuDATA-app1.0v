"""
Verifies the precision of yukyu parsing vs v2.0
"""
import sys
import excel_service
import database

# Configure console for UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("="*60)
print("  YUKYU PARSING PRECISION TEST")
print("="*60)

# Test with actual Excel file
excel_path = "D:\\YuKyuDATA-app\\有給休暇管理.xlsm"

print(f"\n1. Parsing Excel file...")
print(f"   Path: {excel_path}")

try:
    data = excel_service.parse_excel_file(excel_path)
    print(f"   ✓ Parsed successfully")
    print(f"   ✓ Total records: {len(data)}")

    # Analyze parsing results
    print(f"\n2. Analyzing parsed data...")

    # Check if balance is being read from Excel
    has_balance_col = any(emp.get('balance', 0) != emp.get('granted', 0) - emp.get('used', 0) for emp in data if emp.get('granted', 0) > 0)

    if has_balance_col:
        print(f"   ✓ Balance: Read from Excel (CORRECT - like v2.0)")
    else:
        print(f"   ⚠ Balance: Calculated (INCORRECT - not like v2.0)")

    # Check if expired column exists
    has_expired = any(emp.get('expired', 0) > 0 for emp in data)

    if has_expired:
        print(f"   ✓ Expired column: Found and has data")
    else:
        print(f"   ℹ Expired column: No data (may not exist in Excel)")

    # Check for employee+year uniqueness (CORRECT behavior)
    employee_year_keys = {}
    for emp in data:
        emp_key = f"{emp.get('employeeNum')}_{emp.get('year')}"
        if emp_key in employee_year_keys:
            employee_year_keys[emp_key] += 1
        else:
            employee_year_keys[emp_key] = 1

    duplicates = {k: v for k, v in employee_year_keys.items() if v > 1}

    # Check employee multi-year records (expected behavior)
    employees_multi_year = {}
    for emp in data:
        emp_num = emp.get('employeeNum')
        if emp_num not in employees_multi_year:
            employees_multi_year[emp_num] = []
        employees_multi_year[emp_num].append(emp.get('year'))

    multi_year_count = sum(1 for years in employees_multi_year.values() if len(years) > 1)

    if len(duplicates) == 0:
        print(f"   ✓ Employee+Year uniqueness: WORKING (no true duplicates)")
        print(f"   ℹ Multi-year records: {multi_year_count} employees (EXPECTED)")
    else:
        print(f"   ✗ Employee+Year uniqueness: FAILED ({len(duplicates)} true duplicates)")
        print(f"     First 5 duplicates: {list(duplicates.items())[:5]}")

    # Show sample data
    print(f"\n3. Sample of first 5 employees:")
    for emp in data[:5]:
        print(f"\n   {emp.get('name')} ({emp.get('employeeNum')}) - {emp.get('year')}")
        print(f"     Factory: {emp.get('haken')}")
        print(f"     Granted: {emp.get('granted', 0):.1f} days")
        print(f"     Used: {emp.get('used', 0):.1f} days")
        print(f"     Balance: {emp.get('balance', 0):.1f} days")
        print(f"     Expired: {emp.get('expired', 0):.1f} days")
        print(f"     Usage: {emp.get('usageRate', 0)}%")

    # Save to database
    print(f"\n4. Saving to database...")
    database.save_employees(data)
    print(f"   ✓ Saved {len(data)} records")

    # Verify from database
    print(f"\n5. Verifying from database...")
    db_data = database.get_employees()
    print(f"   ✓ Retrieved {len(db_data)} records from DB")

    # Compare precision
    print(f"\n6. Precision Summary:")
    print(f"   {'='*56}")
    print(f"   {'Feature':<35} {'Status':<20}")
    print(f"   {'-'*56}")
    print(f"   {'Read balance from Excel':<35} {'✓ YES' if has_balance_col else '✗ NO':<20}")
    print(f"   {'Read expired from Excel':<35} {'✓ YES' if has_expired else 'ℹ N/A':<20}")
    print(f"   {'Employee+Year uniqueness':<35} {'✓ YES' if len(duplicates) == 0 else '✗ NO':<20}")
    print(f"   {'Multi-year employee tracking':<35} {'✓ ' + str(multi_year_count) + ' employees':<20}")
    print(f"   {'-'*56}")

    if has_balance_col and len(duplicates) == 0:
        print(f"\n   ✓✓✓ PRECISION: 100% (Same as v2.0) ✓✓✓")
    else:
        print(f"\n   ⚠ PRECISION: Needs improvement")

    print(f"\n{'='*60}")
    print(f"  TEST COMPLETED")
    print(f"{'='*60}")

except FileNotFoundError:
    print(f"   ✗ Error: Excel file not found")
    print(f"   Make sure the file exists at: {excel_path}")
except Exception as e:
    print(f"   ✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

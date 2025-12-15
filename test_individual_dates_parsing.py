"""
Test parsing of individual yukyu usage dates from Excel (columns R-BE)
"""
import sys
import excel_service

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("="*70)
print("  TEST: Individual Yukyu Usage Dates Parsing (v2.0 Feature)")
print("="*70)

excel_path = r"D:\YuKyuDATA-app\有給休暇管理.xlsm"

print(f"\n1. Parsing individual usage dates from Excel...")
print(f"   File: {excel_path}")
print(f"   Extracting columns R-BE (18-57) - 40 date columns")

try:
    usage_details = excel_service.parse_yukyu_usage_details(excel_path)
    print(f"\n   ✓ Parsed successfully!")
    print(f"   ✓ Total individual usage records: {len(usage_details)}")

    # Group by year
    from collections import Counter
    year_counts = Counter(detail['year'] for detail in usage_details)

    print(f"\n2. Usage records by year:")
    for year in sorted(year_counts.keys()):
        print(f"   {year}: {year_counts[year]} individual usage dates")

    # Group by month for 2025
    usage_2025 = [d for d in usage_details if d['year'] == 2025]
    if usage_2025:
        month_counts_2025 = Counter(detail['month'] for detail in usage_2025)
        print(f"\n3. 2025 usage breakdown by month:")
        for month in sorted(month_counts_2025.keys()):
            print(f"   {month:2}月: {month_counts_2025[month]:4} days")

    # Show sample of employee usage
    from collections import defaultdict
    employee_usage = defaultdict(list)
    for detail in usage_details:
        employee_usage[detail['employee_num']].append(detail)

    print(f"\n4. Sample employee usage patterns (first 5 employees):")
    for i, (emp_num, details) in enumerate(list(employee_usage.items())[:5], 1):
        emp_name = details[0]['name']
        total_days = len(details)
        dates = sorted([d['use_date'] for d in details])

        print(f"\n   {i}. {emp_name} ({emp_num})")
        print(f"      Total days used: {total_days}")
        print(f"      Dates: {', '.join(dates[:10])}")
        if len(dates) > 10:
            print(f"      ... and {len(dates) - 10} more dates")

    # Summary
    unique_employees = len(employee_usage)
    print(f"\n5. Summary:")
    print(f"   Total individual usage records: {len(usage_details)}")
    print(f"   Unique employees with usage: {unique_employees}")
    print(f"   Average days per employee: {len(usage_details) / unique_employees:.1f}")

    print(f"\n{'='*70}")
    print(f"  ✓✓✓ Individual dates parsing WORKING!")
    print(f"{'='*70}")

except Exception as e:
    print(f"\n   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

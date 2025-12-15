"""
Check data count discrepancy
"""
import sys
import database
import excel_service

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("="*60)
print("  DATA COUNT INVESTIGATION")
print("="*60)

# 1. Check what's in the database
print("\n1. DATABASE COUNT:")
db_data = database.get_employees()
print(f"   Total records in DB: {len(db_data)}")

# Count by year
from collections import Counter
year_counts = Counter(emp['year'] for emp in db_data)
print(f"\n   Records by year:")
for year in sorted(year_counts.keys()):
    print(f"     {year}: {year_counts[year]} records")

# Count unique employees
unique_employees = len(set(emp['employee_num'] for emp in db_data))
print(f"\n   Unique employees: {unique_employees}")

# 2. Check what Excel parsing returns
print("\n2. EXCEL PARSING COUNT:")
excel_path = "D:\\YuKyuDATA-app\\有給休暇管理.xlsm"
try:
    excel_data = excel_service.parse_excel_file(excel_path)
    print(f"   Total records from Excel: {len(excel_data)}")

    # Count by year from Excel
    excel_year_counts = Counter(emp['year'] for emp in excel_data)
    print(f"\n   Records by year from Excel:")
    for year in sorted(excel_year_counts.keys()):
        print(f"     {year}: {excel_year_counts[year]} records")

    # Unique employees from Excel
    unique_excel_employees = len(set(emp['employeeNum'] for emp in excel_data))
    print(f"\n   Unique employees from Excel: {unique_excel_employees}")
except Exception as e:
    print(f"   Error reading Excel: {e}")

# 3. Show what the frontend sees
print("\n3. WHAT FRONTEND GETS:")
print("   Endpoint: GET /api/employees")
all_employees = database.get_employees()
print(f"   Returns: {len(all_employees)} records")

# Check available years
available_years = database.get_available_years()
print(f"\n   Available years: {available_years}")
print(f"   Number of years: {len(available_years)}")

# 4. Show sample to understand structure
print("\n4. SAMPLE DATA (first employee, all years):")
if db_data:
    first_emp_num = db_data[0]['employee_num']
    emp_records = [e for e in db_data if e['employee_num'] == first_emp_num]
    print(f"\n   Employee: {emp_records[0]['name']} ({first_emp_num})")
    print(f"   Total records for this employee: {len(emp_records)}")
    for rec in emp_records:
        print(f"     {rec['year']}: granted={rec['granted']}, used={rec['used']}, balance={rec['balance']}")

print("\n" + "="*60)
print("  ANALYSIS COMPLETE")
print("="*60)

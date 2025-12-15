"""
Analyze 2025 yukyu usage breakdown by employee type
"""
import sys
import database

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("="*70)
print("  2025年 有給使用状況 - 従業員タイプ別分析")
print("="*70)

# Get all yukyu data for 2025
yukyu_2025 = database.get_employees(year=2025)
print(f"\n📊 2025年 総データ:")
print(f"   総レコード数: {len(yukyu_2025)}")
total_used_2025 = sum(emp['used'] for emp in yukyu_2025)
print(f"   総使用日数: {total_used_2025:.1f} 日")

# Get employee lists from genzai and ukeoi
genzai_employees = database.get_genzai()  # 派遣社員
ukeoi_employees = database.get_ukeoi()    # 請負社員

# Create sets of employee numbers for quick lookup
genzai_nums = {emp['employee_num'] for emp in genzai_employees if emp.get('employee_num')}
ukeoi_nums = {emp['employee_num'] for emp in ukeoi_employees if emp.get('employee_num')}

print(f"\n📋 従業員マスターデータ:")
print(f"   派遣社員 (Genzai): {len(genzai_nums)} 名")
print(f"   請負社員 (Ukeoi): {len(ukeoi_nums)} 名")

# Classify yukyu records by employee type
hakenshain_usage = []  # 派遣社員
ukeoi_usage = []       # 請負社員
staff_usage = []       # スタッフ (others)
unknown_usage = []     # 不明

for emp in yukyu_2025:
    emp_num = str(emp['employee_num']) if emp['employee_num'] else None

    if emp_num in genzai_nums:
        hakenshain_usage.append(emp)
    elif emp_num in ukeoi_nums:
        ukeoi_usage.append(emp)
    elif emp_num:
        staff_usage.append(emp)
    else:
        unknown_usage.append(emp)

# Calculate totals
hakenshain_days = sum(emp['used'] for emp in hakenshain_usage)
ukeoi_days = sum(emp['used'] for emp in ukeoi_usage)
staff_days = sum(emp['used'] for emp in staff_usage)
unknown_days = sum(emp['used'] for emp in unknown_usage)

print(f"\n{'='*70}")
print(f"  2025年 使用日数内訳 (従業員タイプ別)")
print(f"{'='*70}")

print(f"\n🏢 派遣社員 (Hakenshain/Genzai):")
print(f"   従業員数: {len(hakenshain_usage)} 名")
print(f"   使用日数: {hakenshain_days:.1f} 日")
print(f"   割合: {(hakenshain_days/total_used_2025*100):.1f}%")

print(f"\n🔧 請負社員 (Ukeoi):")
print(f"   従業員数: {len(ukeoi_usage)} 名")
print(f"   使用日数: {ukeoi_days:.1f} 日")
print(f"   割合: {(ukeoi_days/total_used_2025*100):.1f}%")

print(f"\n👔 スタッフ/その他 (Staff/Others):")
print(f"   従業員数: {len(staff_usage)} 名")
print(f"   使用日数: {staff_days:.1f} 日")
print(f"   割合: {(staff_days/total_used_2025*100):.1f}%")

if unknown_days > 0:
    print(f"\n❓ 不明 (Unknown):")
    print(f"   従業員数: {len(unknown_usage)} 名")
    print(f"   使用日数: {unknown_days:.1f} 日")

print(f"\n{'='*70}")
print(f"  合計検証")
print(f"{'='*70}")
calculated_total = hakenshain_days + ukeoi_days + staff_days + unknown_days
print(f"   計算合計: {calculated_total:.1f} 日")
print(f"   実際合計: {total_used_2025:.1f} 日")
print(f"   差分: {abs(calculated_total - total_used_2025):.1f} 日")

# Show top users by type
print(f"\n{'='*70}")
print(f"  Top 5 使用者 (各タイプ別)")
print(f"{'='*70}")

print(f"\n🏢 派遣社員 Top 5:")
top_haken = sorted(hakenshain_usage, key=lambda x: x['used'], reverse=True)[:5]
for i, emp in enumerate(top_haken, 1):
    print(f"   {i}. {emp['name']:<20} {emp['used']:>6.1f}日 ({emp['haken']})")

print(f"\n🔧 請負社員 Top 5:")
top_ukeoi = sorted(ukeoi_usage, key=lambda x: x['used'], reverse=True)[:5]
for i, emp in enumerate(top_ukeoi, 1):
    print(f"   {i}. {emp['name']:<20} {emp['used']:>6.1f}日 ({emp['haken']})")

if staff_usage:
    print(f"\n👔 スタッフ Top 5:")
    top_staff = sorted(staff_usage, key=lambda x: x['used'], reverse=True)[:5]
    for i, emp in enumerate(top_staff, 1):
        print(f"   {i}. {emp['name']:<20} {emp['used']:>6.1f}日 ({emp['haken']})")

print(f"\n{'='*70}")
print(f"  分析完了")
print(f"{'='*70}")

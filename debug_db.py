from database import get_db, get_employees, get_genzai, get_yukyu_usage_details

def debug():
    print("--- DEBUG START ---")
    
    try:
        print("Calling get_genzai()...")
        genzai_list = get_genzai()
        print(f"get_genzai success. Count: {len(genzai_list)}")
        
        target = next((g for g in genzai_list if g['employee_num'] == '220108'), None)
        if target:
             print(f"Genzai 220108: Name='{target.get('name')}', Kana='{target.get('kana')}'")
        else:
             print("Genzai 220108 not found in list")
             
    except Exception as e:
        print(f"!!! get_genzai FAILED: {e}")
        import traceback
        traceback.print_exc()

    try:
        print("\nCalling get_employees()...")
        emps = get_employees(year=2026)
        print(f"get_employees success. Count: {len(emps)}")
        
        target_emp = next((e for e in emps if e['employee_num'] == '220108'), None)
        if target_emp:
            print(f"get_employees 220108: Name='{target_emp.get('name')}', Kana='{target_emp.get('kana')}'")
        else:
            print("get_employees 220108: NOT FOUND in 2026 filtered list")
            
    except Exception as e:
         print(f"!!! get_employees FAILED: {e}")
         traceback.print_exc()

    print("--- DEBUG END ---")

if __name__ == "__main__":
    debug()

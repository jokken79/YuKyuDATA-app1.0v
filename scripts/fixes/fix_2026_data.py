
import sqlite3
from datetime import datetime

def fix_all_used_days():
    conn = sqlite3.connect('yukyu.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get all employees in 2026
    employees = c.execute("SELECT id, employee_num, year, granted FROM employees WHERE year = 2026").fetchall()
    print(f"Checking {len(employees)} employees for 2026...")
    
    total_fixed = 0
    total_used_2026 = 0
    
    for emp in employees:
        emp_id = emp['id']
        emp_num = emp['employee_num']
        year = emp['year']
        granted = emp['granted'] or 0.0
        
        # Get sum from details for this year
        res = c.execute('''
            SELECT COALESCE(SUM(days_used), 0) as total_used 
            FROM yukyu_usage_details 
            WHERE employee_num = ? AND year = ?
        ''', (emp_num, year)).fetchone()
        
        actual_used = res['total_used']
        new_balance = granted - actual_used
        new_rate = (actual_used / granted * 100) if granted > 0 else 0.0
        
        # Update
        c.execute('''
            UPDATE employees 
            SET used = ?, balance = ?, usage_rate = ?, last_updated = ?
            WHERE id = ?
        ''', (actual_used, new_balance, new_rate, datetime.now().isoformat(), emp_id))
        
        total_used_2026 += actual_used
        total_fixed += 1
        
    conn.commit()
    conn.close()
    print(f"Done. Fixed {total_fixed} records. New total used for 2026: {total_used_2026}")

if __name__ == "__main__":
    fix_all_used_days()

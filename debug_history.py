import sqlite3
import os
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

DB_NAME = 'yukyu.db'

def check_history(emp_num):
    if not os.path.exists(DB_NAME):
        print(f"Database file {DB_NAME} not found!")
        return

    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        print(f"--- CHECKING HISTORY FOR: {emp_num} ---")
        
        # Check employees table
        c.execute("SELECT * FROM employees WHERE employee_num = ?", (emp_num,))
        emp = c.fetchone()
        if emp:
            print(f"Employee Found: {emp['name']} (Term: {emp['year']})")
        else:
            print("Employee NOT found in 'employees' table.")
            
        # Check usage details
        c.execute("SELECT * FROM yukyu_usage_details WHERE employee_num = ? ORDER BY use_date DESC", (emp_num,))
        rows = c.fetchall()
        
        if rows:
            print(f"Total Usage Records Found: {len(rows)}")
            print("Recent 5 records:")
            for i, row in enumerate(rows[:5]):
                print(f"  {i+1}. Date: {row['use_date']}, Days: {row['days_used']}")
        else:
            print("No usage history found in 'yukyu_usage_details' table.")
            
        conn.close()
        print("--- END CHECK ---")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_history('230101')


import sqlite3

conn = sqlite3.connect('d:/YuKyuDATA-app/yukyu.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

rows = c.execute("SELECT * FROM employees").fetchall()
employees = [dict(r) for r in rows]

granted_zero = [e for e in employees if e['granted'] == 0]

print(f"--- Employees with Granted == 0 ({len(granted_zero)}) ---")
for e in granted_zero:
    print(f"ID: {e['employee_num']}, Name: {e['name']}, Haken: {e['haken']}, Granted: {e['granted']}, Used: {e['used']}")

conn.close()

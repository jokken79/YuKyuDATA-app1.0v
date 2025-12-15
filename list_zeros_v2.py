
import sqlite3

conn = sqlite3.connect('d:/YuKyuDATA-app/yukyu.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

rows = c.execute("SELECT * FROM employees").fetchall()
employees = [dict(r) for r in rows]

granted_zero = [e for e in employees if e['granted'] == 0]

with open('d:/YuKyuDATA-app/zeros_output.txt', 'w', encoding='utf-8') as f:
    f.write(f"--- Employees with Granted == 0 ({len(granted_zero)}) ---\n")
    for e in granted_zero:
        f.write(f"ID: {e['employee_num']}, Name: {e['name']}, Haken: {e['haken']}, Granted: {e['granted']}, Used: {e['used']}\n")

conn.close()

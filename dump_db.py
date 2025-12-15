
import sqlite3
import json

conn = sqlite3.connect('d:/YuKyuDATA-app/yukyu.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

rows = c.execute("SELECT * FROM employees ORDER BY employee_num").fetchall()
employees = [dict(r) for r in rows]

with open('d:/YuKyuDATA-app/employees_dump.json', 'w', encoding='utf-8') as f:
    json.dump(employees, f, ensure_ascii=False, indent=2)

print(f"Dumped {len(employees)} employees to employees_dump.json")
conn.close()


import sqlite3

conn = sqlite3.connect('d:/YuKyuDATA-app/yukyu.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

rows = c.execute("SELECT * FROM employees").fetchall()
employees = [dict(r) for r in rows]

head_office = [e for e in employees if e['haken'] == '高雄工業 本社']
duplicate_guy = [e for e in employees if e['name'] == 'DONG NGOC SON']

print(f"--- Head Office Employees ({len(head_office)}) ---")
for e in head_office:
    print(f"ID: {e['employee_num']}, Name: {e['name']}, Haken: {e['haken']}")

print(f"\n--- Duplicate Guy Details ---")
for e in duplicate_guy:
    print(f"ID: {e['employee_num']}, Name: {e['name']}, Haken: {e['haken']}")

conn.close()

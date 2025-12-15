
import sqlite3

conn = sqlite3.connect('d:/YuKyuDATA-app/yukyu.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

rows = c.execute("SELECT * FROM employees").fetchall()
employees = [dict(r) for r in rows]

head_office = [e for e in employees if e['haken'] == '高雄工業 本社']
duplicate_guy = [e for e in employees if e['name'] == 'DONG NGOC SON']

with open('d:/YuKyuDATA-app/head_office_debug.txt', 'w', encoding='utf-8') as f:
    f.write(f"--- Head Office Employees ({len(head_office)}) ---\n")
    for e in head_office:
        f.write(f"ID: {e['employee_num']}, Name: {e['name']}, Haken: {e['haken']}\n")

    f.write(f"\n--- Duplicate Guy Details ---\n")
    for e in duplicate_guy:
        f.write(f"ID: {e['employee_num']}, Name: {e['name']}, Haken: {e['haken']}\n")

conn.close()

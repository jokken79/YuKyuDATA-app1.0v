
import sqlite3
from collections import Counter

conn = sqlite3.connect('d:/YuKyuDATA-app/yukyu.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

rows = c.execute("SELECT * FROM employees").fetchall()
employees = [dict(r) for r in rows]

names = [e['name'] for e in employees]
counts = Counter(names)

duplicates = {n: c for n, c in counts.items() if c > 1}

print(f"--- Duplicate Names ({len(duplicates)}) ---")
for name, count in duplicates.items():
    print(f"Name: {name}, Count: {count}")
    # Print details for these duplicates
    dupes = [e for e in employees if e['name'] == name]
    for d in dupes:
        print(f"  ID: {d['employee_num']}, Granted: {d['granted']}")

conn.close()

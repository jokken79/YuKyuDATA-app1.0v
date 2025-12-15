
import sqlite3
from collections import Counter

conn = sqlite3.connect('d:/YuKyuDATA-app/yukyu.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

rows = c.execute("SELECT * FROM employees").fetchall()
employees = [dict(r) for r in rows]

haken_counts = Counter([e['haken'] for e in employees])

with open('d:/YuKyuDATA-app/haken_dist.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total Employees: {len(employees)}\n")
    for h, c in haken_counts.most_common():
        f.write(f"{h}: {c}\n")

conn.close()


import sqlite3

conn = sqlite3.connect('d:/YuKyuDATA-app/yukyu.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

rows = c.execute("SELECT * FROM employees").fetchall()
employees = [dict(r) for r in rows]

granted_zero = [e for e in employees if e['granted'] == 0]
granted_and_used_zero = [e for e in employees if e['granted'] == 0 and e['used'] == 0]

print(f"Total employees: {len(employees)}")
print(f"Employees with granted == 0: {len(granted_zero)}")
print(f"Employees with granted == 0 AND used == 0: {len(granted_and_used_zero)}")

total_granted = sum(e['granted'] for e in employees)
print(f"Total granted days (calc): {total_granted}")

# If we remove granted==0, what is the count?
print(f"Count if excluding granted==0: {len(employees) - len(granted_zero)}")

conn.close()

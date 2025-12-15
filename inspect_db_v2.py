
import sqlite3

conn = sqlite3.connect('d:/YuKyuDATA-app/yukyu.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

rows = c.execute("SELECT * FROM employees").fetchall()
print(f"Total count: {len(rows)}")

years = {}
for r in rows:
    y = r['year']
    years[y] = years.get(y, 0) + 1

print(f"Years: {years}")

print("\n--- Listing Potential Non-Employees (weird IDs or Names) ---")
for r in rows:
    # Check for non-digit IDs or empty names or 'total' in name
    if not r['employee_num'].isdigit() or not r['name']:
        print(dict(r))

print("\n--- Listing 7 possibly extra records ---")
# If there are exactly 96, let's look at the ones that might be 'inactive' or 'retired' if we can find a flag. 
# There is no status column in the schema shown earlier, only:
# id, employee_num, name, haken, granted, used, balance, usage_rate, year, last_updated
# 'haken' column might contain status?

count_by_haken = {}
for r in rows:
    h = r['haken']
    count_by_haken[h] = count_by_haken.get(h, 0) + 1
print(f"Haken distribution: {count_by_haken}")

conn.close()

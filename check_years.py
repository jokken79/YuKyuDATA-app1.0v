import sqlite3

conn = sqlite3.connect('yukyu.db')
c = conn.cursor()
try:
    c.execute("SELECT year, COUNT(*) FROM employees GROUP BY year")
    rows = c.fetchall()
    print("Year Distribution:")
    for r in rows:
        print(f"Year {r[0]}: {r[1]} records")
except Exception as e:
    print(e)
finally:
    conn.close()

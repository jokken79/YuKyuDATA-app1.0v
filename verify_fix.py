
import sqlite3
import excel_service
import database
import os

# 1. Clear current DB to be sure
# database.clear_database() # Optional, but safer to test sync logic which does replace
# Actually, sync does INSERT OR REPLACE. If we want to test that old ones are gone, we might need to clear or check if they remain given they won't be in the new list.
# The user's goal is to see 89 on dashboard. If we just update, the 7 old ones might remain if we don't clear or if the app doesn't handle "deletion" of missing records.
# Let's check `database.py`. It has `clear_database`. 
# The `sync` endpoint does: parse -> save_employees. save_employees does INSERT OR REPLACE. It DOES NOT delete records not in the list.
# So if we just run sync, the 7 formatted-out employees will REMAIN in the db with old data.
# We MUST clear the database first or rely on a "full sync" that handles deletions (which current code doesn't seems to do).
# Let's clear it in this script to prove the parser works.

print("Clearing database...")
database.clear_database()

print("Parsing Excel...")
file_path = r"D:\YuKyuDATA-app\有給休暇管理.xlsm"
data = excel_service.parse_excel_file(file_path)

print(f"Parsed {len(data)} employees.")

print("Saving to database...")
database.save_employees(data)

# Verify count in DB
conn = sqlite3.connect('d:/YuKyuDATA-app/yukyu.db')
c = conn.cursor()
count = c.execute("SELECT Count(*) FROM employees").fetchone()[0]
print(f"Database count: {count}")
conn.close()

if count == 89:
    print("SUCCESS: Count is 89.")
else:
    print(f"FAILURE: Count is {count}. Expected 89.")

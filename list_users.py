import sqlite3
import os

db_path = 'yukyu.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if cursor.fetchone():
            cursor.execute("SELECT username, role, is_active FROM users;")
            rows = cursor.fetchall()
            for row in rows:
                print(f"User: {row[0]}, Role: {row[1]}, Active: {row[2]}")
        else:
            print("Table 'users' does not exist.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database {db_path} not found.")

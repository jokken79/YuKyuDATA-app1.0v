"""
Recreates the database with the new 'expired' column
"""
import os
import sys
import database

# Configure console for UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Backup old database if exists
if os.path.exists('yukyu.db'):
    print("Backing up old database...")
    if os.path.exists('yukyu.db.backup'):
        os.remove('yukyu.db.backup')
    os.rename('yukyu.db', 'yukyu.db.backup')
    print("  ✓ Old database backed up to yukyu.db.backup")

# Initialize new database with updated schema
print("\nCreating new database with 'expired' column...")
database.init_db()
print("  ✓ Database created successfully!")

print("\nNew schema includes:")
print("  - id, employee_num, name, haken")
print("  - granted, used, balance")
print("  - expired  ← NEW COLUMN")
print("  - usage_rate, year, last_updated")

print("\n✓ Database ready for synchronization")
print("\nNext steps:")
print("  1. Open http://localhost:8888 in browser")
print("  2. Click '自動同期' to sync from Excel")
print("  3. Verify data shows correctly with new precision")

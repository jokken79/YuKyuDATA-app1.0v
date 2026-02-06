
import sys
import os
from sqlalchemy import inspect, text

# Add project root to path
sys.path.append(os.getcwd())

from orm import engine

def migrate():
    print("Starting migration...")
    insp = inspect(engine)
    with engine.connect() as conn:
        tables = insp.get_table_names()
        
        target_tables = [
            'employees', 'yukyu_usage_details', 'genzai', 'ukeoi', 'staff',
            'leave_requests', 'audit_log', 'notification_reads', 'notifications', 'referesh_tokens', 'users'
        ]
        
        # Also check 'refresh_tokens' (spelled correctly) if it exists
        if 'refresh_tokens' in tables:
            target_tables.append('refresh_tokens')

        for table in target_tables:
            if table not in tables:
                continue
                
            print(f"Checking {table}...")
            columns = [c['name'] for c in insp.get_columns(table)]
            
            # Check for created_at
            if 'created_at' not in columns:
                print(f"Migrating {table}: Adding created_at column...")
                try:
                    if 'sqlite' in str(engine.url):
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                    else:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN created_at TIMESTAMP DEFAULT NOW()"))
                except Exception as e:
                    print(f"Migration error for {table}.created_at: {e}")

            # Check for updated_at
            if 'updated_at' not in columns:
                print(f"Migrating {table}: Adding updated_at column...")
                try:
                    if 'sqlite' in str(engine.url):
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                    else:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()"))
                except Exception as e:
                    print(f"Migration error for {table}.updated_at: {e}")

        conn.commit()
    print("Migration complete.")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"FATAL ERROR: {e}")

from sqlalchemy import inspect, text
from orm import engine, Base
# Import all models to ensure they are registered with Base
from orm.models import (
    Employee, 
    YukyuUsageDetail, 
    GenzaiEmployee, 
    UkeoiEmployee, 
    StaffEmployee,
    LeaveRequest,
    AuditLog,
    Notification,
    NotificationRead,
    User
)

def init_db():
    """
    Initialize database using SQLAlchemy ORM.
    Also performs basic schema migration for existing tables.
    """
    # Create all tables defined in ORM models
    Base.metadata.create_all(bind=engine)
    
    # Perform migration for legacy tables (sqlite check)
    insp = inspect(engine)
    with engine.connect() as conn:
        tables = insp.get_table_names()
        
        # List of tables that should have BaseModel fields
        target_tables = [
            'employees', 'yukyu_usage_details', 'genzai', 'ukeoi', 'staff',
            'leave_requests', 'audit_log', 'notification_reads', 'notifications', 'users'
        ]
        
        for table in target_tables:
            if table in tables:
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

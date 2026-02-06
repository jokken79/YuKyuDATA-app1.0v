
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    print("Testing imports...")
    from database import (
        get_db, USE_POSTGRESQL, init_db,
        save_employees, save_employee_data, get_employees,
        save_leave_request, get_leave_requests, save_yukyu_usage_details,
        log_audit_action, get_audit_logs,
        create_notification, get_notifications,
        get_dashboard_stats
    )
    from orm import SessionLocal, Employee, LeaveRequest, AuditLog
    
    print("Imports successful!")
    
    # Initialize DB (creates sqlite file if needed)
    print("Initializing Database...")
    init_db()
    
    # Simple ORM test
    print("Testing ORM Session...")
    with SessionLocal() as session:
        # Check if we can query
        count = session.query(Employee).count()
        print(f"Employee count: {count}")

        # Create a test audit log
        print("Testing log_audit_action...")
        log_audit_action(
            user_id="test_script",
            action="TEST_VERIFY",
            entity_type="SYSTEM",
            additional_info="Verification script run"
        )
        
        # Verify log exists
        logs = get_audit_logs(entity_type="SYSTEM", limit=1)
        if logs and logs[0]['action'] == 'TEST_VERIFY':
            print("Audit log verification successful!")
        else:
            print("Audit log verification FAILED")
            
    print("verification complete.")
    
except Exception as e:
    print(f"Verification FAILED with error: {e}")
    import traceback
    traceback.print_exc()

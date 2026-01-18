import asyncio
import logging
from services import excel_service
import database
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verify database connection
try:
    with database.get_db() as conn:
        print("Database connection successful.")
except Exception as e:
    print(f"Database connection failed: {e}")
    exit(1)

DEFAULT_EXCEL_PATH = Path("c:/Users/Jpkken/Appsdenuevo/YuKyuDATA-app1.0v/data/input/employee_data.xlsx") # Adjust path if needed

async def seed():
    excel_path = DEFAULT_EXCEL_PATH
    print(f"Seeding data from {excel_path}...")
    if not excel_path.exists():
        print(f"Error: {excel_path} does not exist.")
        # Try to find it
        common_paths = [
            Path("【新】社員台帳(UNS)T　2022.04.05～.xlsm"),
            Path("有給休暇管理.xlsm"),
            Path("data/input/employee_data.xlsx"),
            Path("employee_data.xlsx"),
            Path("c:/Users/Jpkken/Appsdenuevo/YuKyuDATA-app1.0v/data/input/employee_data.xlsx")
        ]
        for p in common_paths:
            if p.exists():
                print(f"Found at {p}")
                excel_path = p
                break
        else:
             return

    # Sync Employees (Main)
    try:
        print("Parsing Employees...")
        data = excel_service.parse_excel_file(excel_path)
        database.save_employees(data)
        print(f"Saved {len(data)} employees.")
    except Exception as e:
        print(f"Error parsing employees: {e}")

    # Sync Usage Details
    try:
        print("Parsing Usage Details...")
        usage = excel_service.parse_yukyu_usage_details(excel_path)
        database.save_yukyu_usage_details(usage)
        print(f"Saved {len(usage)} usage details.")
    except Exception as e:
        print(f"Error parsing usage: {e}")

    # Sync Genzai
    try:
        print("Parsing Genzai...")
        genzai = excel_service.parse_genzai_sheet(excel_path)
        database.save_genzai(genzai)
        print(f"Saved {len(genzai)} genzai records.")
    except Exception as e:
        print(f"Error parsing Genzai: {e}")

    # Sync Ukeoi
    try:
        print("Parsing Ukeoi...")
        ukeoi = excel_service.parse_ukeoi_sheet(excel_path)
        database.save_ukeoi(ukeoi)
        print(f"Saved {len(ukeoi)} ukeoi records.")
    except Exception as e:
        print(f"Error parsing Ukeoi: {e}")

    # Sync Staff
    try:
        print("Parsing Staff...")
        staff = excel_service.parse_staff_sheet(excel_path)
        if hasattr(database, 'save_staff'):
            database.save_staff(staff)
            print(f"Saved {len(staff)} staff records.")
        else:
            print("database.save_staff not found.")
    except Exception as e:
        print(f"Error parsing Staff: {e}")

if __name__ == "__main__":
    asyncio.run(seed())

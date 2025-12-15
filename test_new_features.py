"""
Test script for new Genzai and Ukeoi features
"""
import sys
import excel_service
import database

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

EMPLOYEE_REGISTRY_PATH = r"D:\YuKyuDATA-app\【新】社員台帳(UNS)T　2022.04.05～.xlsm"

def test_genzai():
    print("=== Testing Genzai (DBGenzaiX) ===")
    try:
        # Initialize DB
        database.init_db()

        # Parse Genzai sheet
        print("Parsing DBGenzaiX sheet...")
        data = excel_service.parse_genzai_sheet(EMPLOYEE_REGISTRY_PATH)
        print(f"[OK] Parsed {len(data)} dispatch employees")

        if data:
            print(f"\nSample employee:")
            sample = data[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")

        # Save to database
        print(f"\nSaving to database...")
        database.save_genzai(data)
        print(f"[OK] Saved {len(data)} employees to genzai table")

        # Retrieve from database
        print(f"\nRetrieving from database...")
        retrieved = database.get_genzai()
        print(f"[OK] Retrieved {len(retrieved)} employees from genzai table")

        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ukeoi():
    print("\n=== Testing Ukeoi (DBUkeoiX) ===")
    try:
        # Parse Ukeoi sheet
        print("Parsing DBUkeoiX sheet...")
        data = excel_service.parse_ukeoi_sheet(EMPLOYEE_REGISTRY_PATH)
        print(f"[OK] Parsed {len(data)} contract employees")

        if data:
            print(f"\nSample employee:")
            sample = data[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")

        # Save to database
        print(f"\nSaving to database...")
        database.save_ukeoi(data)
        print(f"[OK] Saved {len(data)} employees to ukeoi table")

        # Retrieve from database
        print(f"\nRetrieving from database...")
        retrieved = database.get_ukeoi()
        print(f"[OK] Retrieved {len(retrieved)} employees from ukeoi table")

        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing new Genzai and Ukeoi features\n")

    genzai_ok = test_genzai()
    ukeoi_ok = test_ukeoi()

    print("\n" + "="*50)
    print("RESULTS:")
    print(f"  Genzai: {'PASS' if genzai_ok else 'FAIL'}")
    print(f"  Ukeoi:  {'PASS' if ukeoi_ok else 'FAIL'}")
    print("="*50)

"""
Complete system test - Verifies all functionality
"""
import sys
import requests
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

API_BASE = "http://localhost:8000/api"

def test_server_running():
    """Check if server is running"""
    print("=== Testing Server Connection ===")
    try:
        response = requests.get(f"{API_BASE}/employees", timeout=5)
        print(f"[OK] Server is running (status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("[ERROR] Server is NOT running!")
        print("Please start the server with: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

def test_vacation_sync():
    """Test vacation data sync"""
    print("\n=== Testing Vacation Data Sync ===")
    try:
        response = requests.post(f"{API_BASE}/sync", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Synced {data.get('count', 0)} vacation records")
            return True
        else:
            print(f"[ERROR] Sync failed: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_vacation_data():
    """Test retrieving vacation data"""
    print("\n=== Testing Vacation Data Retrieval ===")
    try:
        response = requests.get(f"{API_BASE}/employees", timeout=10)
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('data', []))
            years = data.get('available_years', [])
            print(f"[OK] Retrieved {count} vacation records")
            print(f"[OK] Available years: {years}")

            # Test year filtering
            if years:
                year = years[0]
                response = requests.get(f"{API_BASE}/employees?year={year}", timeout=10)
                if response.status_code == 200:
                    filtered = response.json()
                    print(f"[OK] Filtered by year {year}: {len(filtered.get('data', []))} records")
            return True
        else:
            print(f"[ERROR] Failed: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_genzai_sync():
    """Test genzai sync"""
    print("\n=== Testing Genzai Sync ===")
    try:
        response = requests.post(f"{API_BASE}/sync-genzai", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] {data.get('message', 'Success')}")
            print(f"[OK] Synced {data.get('count', 0)} dispatch employees")
            return True
        else:
            print(f"[ERROR] Sync failed: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_genzai_data():
    """Test retrieving genzai data"""
    print("\n=== Testing Genzai Data Retrieval ===")
    try:
        response = requests.get(f"{API_BASE}/genzai", timeout=10)
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"[OK] Retrieved {count} dispatch employees")

            # Show sample
            if data.get('data') and len(data['data']) > 0:
                sample = data['data'][0]
                print(f"\nSample dispatch employee:")
                print(f"  Name: {sample.get('name')}")
                print(f"  Employee #: {sample.get('employee_num')}")
                print(f"  Status: {sample.get('status')}")
                print(f"  Dispatch: {sample.get('dispatch_name')}")
            return True
        else:
            print(f"[ERROR] Failed: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_ukeoi_sync():
    """Test ukeoi sync"""
    print("\n=== Testing Ukeoi Sync ===")
    try:
        response = requests.post(f"{API_BASE}/sync-ukeoi", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] {data.get('message', 'Success')}")
            print(f"[OK] Synced {data.get('count', 0)} contract employees")
            return True
        else:
            print(f"[ERROR] Sync failed: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_ukeoi_data():
    """Test retrieving ukeoi data"""
    print("\n=== Testing Ukeoi Data Retrieval ===")
    try:
        response = requests.get(f"{API_BASE}/ukeoi", timeout=10)
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"[OK] Retrieved {count} contract employees")

            # Show sample
            if data.get('data') and len(data['data']) > 0:
                sample = data['data'][0]
                print(f"\nSample contract employee:")
                print(f"  Name: {sample.get('name')}")
                print(f"  Employee #: {sample.get('employee_num')}")
                print(f"  Status: {sample.get('status')}")
                print(f"  Business: {sample.get('contract_business')}")
            return True
        else:
            print(f"[ERROR] Failed: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("COMPLETE SYSTEM TEST")
    print("="*60)

    results = {}

    # Test 1: Server running
    results['server'] = test_server_running()
    if not results['server']:
        print("\n[CRITICAL] Server is not running. Cannot continue tests.")
        sys.exit(1)

    time.sleep(1)

    # Test 2: Vacation sync and retrieval
    results['vacation_sync'] = test_vacation_sync()
    time.sleep(1)
    results['vacation_data'] = test_vacation_data()

    # Test 3: Genzai sync and retrieval
    results['genzai_sync'] = test_genzai_sync()
    time.sleep(1)
    results['genzai_data'] = test_genzai_data()

    # Test 4: Ukeoi sync and retrieval
    results['ukeoi_sync'] = test_ukeoi_sync()
    time.sleep(1)
    results['ukeoi_data'] = test_ukeoi_data()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    all_passed = True
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        symbol = "[OK]" if passed else "[X]"
        print(f"{symbol} {test_name.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False

    print("="*60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED - See details above")
    print("="*60)

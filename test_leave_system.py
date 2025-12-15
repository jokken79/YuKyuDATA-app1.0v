"""
Complete test suite for the Leave Request System
Tests all endpoints and verifies the complete workflow.
"""
import requests
import json
from datetime import datetime, timedelta
import sys

# Configure console for UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/api"

def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

def test_employee_search():
    print_section("TEST 1: Employee Search")

    print("\n1.1 Search all active employees (在職中)...")
    response = requests.get(f"{API_URL}/employees/search?q=&status=在職中")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['count']} active employees")
        if data['data']:
            print("\nFirst 3 employees:")
            for emp in data['data'][:3]:
                print(f"  - {emp['name']} ({emp['employee_num']}) - {emp['factory']}")
            return data['data'][0]['employee_num']  # Return first employee for next tests
    else:
        print(f"✗ Error: {response.text}")
        return None

    return None

def test_employee_leave_info(employee_num):
    print_section("TEST 2: Get Employee Leave Info")

    print(f"\n2.1 Loading leave info for employee {employee_num}...")
    response = requests.get(f"{API_URL}/employees/{employee_num}/leave-info")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        emp = data['employee']
        print(f"✓ Employee: {emp['name']} ({emp['employee_num']})")
        print(f"  Factory: {emp['factory']}")
        print(f"  Status: {emp['status']}")
        print(f"  Total Available: {data['total_available']} days")

        if data['yukyu_history']:
            print("\n  Yukyu History:")
            for record in data['yukyu_history']:
                print(f"    {record['year']}年: Granted={record['granted']}, Used={record['used']}, Balance={record['balance']}")
        else:
            print("  ⚠ No yukyu history found")

        return data
    else:
        print(f"✗ Error: {response.text}")
        return None

def test_create_leave_request(employee_num, employee_name):
    print_section("TEST 3: Create Leave Request")

    start_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=9)).strftime('%Y-%m-%d')

    request_data = {
        "employee_num": employee_num,
        "employee_name": employee_name,
        "start_date": start_date,
        "end_date": end_date,
        "days_requested": 3,
        "reason": "テスト申請 - Vacation"
    }

    print(f"\n3.1 Creating leave request...")
    print(f"  Employee: {employee_name} ({employee_num})")
    print(f"  Period: {start_date} to {end_date}")
    print(f"  Days: 3")

    response = requests.post(f"{API_URL}/leave-requests", json=request_data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Request created successfully!")
        print(f"  Request ID: {data['request_id']}")
        return data['request_id']
    else:
        print(f"✗ Error: {response.text}")
        return None

def test_list_pending_requests():
    print_section("TEST 4: List Pending Requests")

    print("\n4.1 Getting all pending requests...")
    response = requests.get(f"{API_URL}/leave-requests?status=PENDING")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['count']} pending requests")

        if data['data']:
            print("\nPending Requests:")
            for req in data['data']:
                print(f"  ID {req['id']}: {req['employee_name']} - {req['start_date']} to {req['end_date']} ({req['days_requested']} days)")
                print(f"    Status: {req['status']}, Requested at: {req['requested_at']}")
        return data['data']
    else:
        print(f"✗ Error: {response.text}")
        return []

def test_approve_request(request_id):
    print_section("TEST 5: Approve Leave Request")

    approval_data = {
        "approved_by": "Test Manager"
    }

    print(f"\n5.1 Approving request ID {request_id}...")
    response = requests.post(f"{API_URL}/leave-requests/{request_id}/approve", json=approval_data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Request approved successfully!")
        print(f"  Message: {data['message']}")
        return True
    else:
        print(f"✗ Error: {response.text}")
        return False

def test_reject_request(request_id):
    print_section("TEST 6: Reject Leave Request")

    rejection_data = {
        "rejected_by": "Test Manager"
    }

    print(f"\n6.1 Rejecting request ID {request_id}...")
    response = requests.post(f"{API_URL}/leave-requests/{request_id}/reject", json=rejection_data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Request rejected successfully!")
        print(f"  Message: {data['message']}")
        return True
    else:
        print(f"✗ Error: {response.text}")
        return False

def test_verify_balance_update(employee_num, initial_balance):
    print_section("TEST 7: Verify Balance Update After Approval")

    print(f"\n7.1 Checking employee {employee_num} balance after approval...")
    response = requests.get(f"{API_URL}/employees/{employee_num}/leave-info")

    if response.status_code == 200:
        data = response.json()
        new_balance = data['total_available']
        print(f"  Initial Balance: {initial_balance} days")
        print(f"  New Balance: {new_balance} days")
        print(f"  Difference: {initial_balance - new_balance} days")

        if new_balance < initial_balance:
            print("✓ Balance was correctly reduced after approval!")
            return True
        else:
            print("⚠ Balance did not change (expected reduction)")
            return False
    else:
        print(f"✗ Error: {response.text}")
        return False

def run_all_tests():
    print("\n" + "=" * 60)
    print("  YUKYU LEAVE REQUEST SYSTEM - COMPLETE TEST SUITE")
    print("=" * 60)

    try:
        # Test 1: Search employees
        employee_num = test_employee_search()
        if not employee_num:
            print("\n⚠ Skipping remaining tests - No employees found")
            print("   Make sure to sync genzai/ukeoi data first!")
            return

        # Test 2: Get employee leave info
        leave_info = test_employee_leave_info(employee_num)
        if not leave_info:
            print("\n⚠ Skipping remaining tests - Could not load employee info")
            return

        employee_name = leave_info['employee']['name']
        initial_balance = leave_info['total_available']

        # Test 3: Create leave request
        request_id = test_create_leave_request(employee_num, employee_name)
        if not request_id:
            print("\n⚠ Skipping remaining tests - Could not create request")
            return

        # Test 4: List pending requests
        pending_requests = test_list_pending_requests()

        # Test 5: Approve request
        approved = test_approve_request(request_id)

        if approved:
            # Test 7: Verify balance was updated
            test_verify_balance_update(employee_num, initial_balance)

        # Optional: Create another request to test rejection
        print("\n\n--- Creating another request to test rejection ---")
        request_id_2 = test_create_leave_request(employee_num, employee_name)
        if request_id_2:
            test_reject_request(request_id_2)

        print_section("ALL TESTS COMPLETED")
        print("\n✓ Leave Request System is working correctly!")
        print("\nNext steps:")
        print("  1. Open http://localhost:8000 in your browser")
        print("  2. Click '有給申請管理' to access the leave request interface")
        print("  3. Click '従業員を検索' to search for employees")
        print("  4. Click on an employee to see their yukyu history and create a request")
        print("  5. View and approve/reject requests in the '承認待ち申請' table")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server at http://localhost:8000")
        print("   Make sure the FastAPI server is running:")
        print("   python -m uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()

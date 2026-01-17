"""
Performance testing for YuKyuDATA using Locust.

Targets:
  - 1,000 concurrent users
  - GET /employees: < 500ms (p95)
  - POST /leave-requests: < 1s (p95)
  - Error rate: < 0.1%

Run:
  locust -f tests/performance/load_test.py --headless -u 1000 -r 100 -t 5m
"""

import os
import time
from locust import HttpUser, task, between, constant_pacing, events
from datetime import datetime, timedelta


class YuKyuUser(HttpUser):
    """Simulated user behavior for YuKyuDATA."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Login when the user starts."""
        self.employee_num = f"EMP_{self.client.env.user_id % 1000:03d}"
        self.auth_token = None
        self.login()

    def login(self):
        """Authenticate and get JWT token."""
        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123456"
            },
            name="Login"
        )
        if response.status_code == 200:
            self.auth_token = response.json().get("access_token")
            self.client.headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }

    @task(30)
    def get_employees(self):
        """GET /api/employees - Most common operation."""
        year = 2025
        self.client.get(
            f"/api/employees?year={year}",
            name="GET /api/employees"
        )

    @task(20)
    def search_employees(self):
        """GET /api/employees/search - Search operation."""
        queries = ["test", "001", "太郎", "花子"]
        query = queries[hash(self.client.env.user_id) % len(queries)]
        self.client.get(
            f"/api/employees/search?q={query}&year=2025",
            name="GET /api/employees/search"
        )

    @task(10)
    def get_compliance(self):
        """GET /api/compliance/5day - Compliance check."""
        self.client.get(
            "/api/compliance/5day?year=2025",
            name="GET /api/compliance/5day"
        )

    @task(10)
    def get_analytics(self):
        """GET /api/analytics/stats - Analytics."""
        self.client.get(
            "/api/analytics/stats?year=2025",
            name="GET /api/analytics/stats"
        )

    @task(5)
    def get_notifications(self):
        """GET /api/notifications - Notifications."""
        self.client.get(
            "/api/notifications?limit=10",
            name="GET /api/notifications"
        )

    @task(3)
    def create_leave_request(self):
        """POST /api/leave-requests - Create leave request."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = self.client.post(
            "/api/leave-requests",
            json={
                "employee_num": self.employee_num,
                "start_date": tomorrow,
                "end_date": tomorrow,
                "days_requested": 0.5,
                "leave_type": "full",
                "reason": "Test leave request",
                "year": 2025
            },
            name="POST /api/leave-requests"
        )

    @task(2)
    def get_health(self):
        """GET /api/health - Health check."""
        self.client.get(
            "/api/health",
            name="GET /api/health",
            timeout=5
        )


class AdminUser(HttpUser):
    """Admin user behavior."""

    wait_time = constant_pacing(5)  # Wait exactly 5 seconds between requests

    def on_start(self):
        """Login as admin."""
        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123456"
            }
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.client.headers = {
                "Authorization": f"Bearer {token}"
            }

    @task(3)
    def sync_employees(self):
        """POST /api/sync - Sync employees."""
        self.client.post(
            "/api/sync",
            json={"source": "excel"},
            name="POST /api/sync"
        )

    @task(2)
    def generate_report(self):
        """POST /api/reports/pdf - Generate PDF report."""
        self.client.post(
            "/api/reports/pdf",
            json={
                "year": 2025,
                "format": "pdf"
            },
            timeout=30,
            name="POST /api/reports/pdf"
        )

    @task(1)
    def get_project_status(self):
        """GET /api/project-status - Project status."""
        self.client.get(
            "/api/project-status",
            name="GET /api/project-status"
        )


# Event handlers for statistics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Track request metrics."""
    if exception:
        print(f"FAIL: {name} - {exception}")
    else:
        print(f"OK: {name} - {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start."""
    print("\n" + "="*70)
    print(f"LOAD TEST STARTED: {datetime.now().isoformat()}")
    print("="*70 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test results."""
    stats = environment.stats
    print("\n" + "="*70)
    print("LOAD TEST RESULTS")
    print("="*70)
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Error rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Median response time: {stats.total.get_response_time_percentile(0.5):.2f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print("="*70 + "\n")

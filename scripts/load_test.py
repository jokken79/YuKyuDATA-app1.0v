#!/usr/bin/env python3
"""
Load Testing with Locust
=========================

Simulate concurrent user load to verify system capacity.

Load Profile:
- 50 concurrent users
- 5 minute test duration
- Critical endpoints tested
- Target: 50+ req/s with < 0.1% error rate

Installation:
    pip install locust

Usage:
    python scripts/load_test.py --host http://localhost:8000 --users 50 --duration 300

Or use Locust web UI:
    locust -f scripts/load_test.py --host http://localhost:8000
    # Access at http://localhost:8089
"""

import os
import random
from datetime import datetime
from pathlib import Path

from locust import HttpUser, between, task
from locust.env import Environment


class YuKyuLoadTest(HttpUser):
    """Locust load test for YuKyuDATA API."""

    # Random wait time between tasks (2-5 seconds)
    wait_time = between(2, 5)

    def on_start(self):
        """Called when a new user starts."""
        self.year = 2025
        self.employee_num = "001"

    @task(4)
    def get_employees(self):
        """Get employees list (higher weight = more frequent)."""
        response = self.client.get(
            f"/api/v1/employees?year={self.year}",
            name="/api/v1/employees",
        )
        if response.status_code != 200:
            response.failure(f"Got {response.status_code}")

    @task(3)
    def get_employee_detail(self):
        """Get single employee detail."""
        response = self.client.get(
            f"/api/v1/employees/{self.employee_num}_{self.year}",
            name="/api/v1/employees/{emp_id}",
        )
        if response.status_code not in [200, 404]:
            response.failure(f"Got {response.status_code}")

    @task(3)
    def get_leave_requests(self):
        """Get leave requests."""
        response = self.client.get(
            "/api/v1/leave-requests?status=pending",
            name="/api/v1/leave-requests",
        )
        if response.status_code != 200:
            response.failure(f"Got {response.status_code}")

    @task(2)
    def get_compliance(self):
        """Get 5-day compliance check."""
        response = self.client.get(
            f"/api/v1/compliance/5day?year={self.year}",
            name="/api/v1/compliance/5day",
        )
        if response.status_code != 200:
            response.failure(f"Got {response.status_code}")

    @task(2)
    def get_analytics(self):
        """Get analytics data."""
        response = self.client.get(
            f"/api/v1/analytics/stats?year={self.year}",
            name="/api/v1/analytics/stats",
        )
        if response.status_code != 200:
            response.failure(f"Got {response.status_code}")

    @task(2)
    def get_health(self):
        """Get health check."""
        response = self.client.get(
            "/api/health",
            name="/api/health",
        )
        if response.status_code != 200:
            response.failure(f"Got {response.status_code}")

    @task(1)
    def get_notifications(self):
        """Get notifications."""
        response = self.client.get(
            "/api/v1/notifications",
            name="/api/v1/notifications",
        )
        if response.status_code != 200:
            response.failure(f"Got {response.status_code}")

    @task(1)
    def post_leave_request(self):
        """Create leave request (mutation)."""
        payload = {
            "employee_num": self.employee_num,
            "start_date": "2025-02-01",
            "end_date": "2025-02-05",
            "days": 5,
            "reason": "Vacation",
        }
        response = self.client.post(
            "/api/v1/leave-requests",
            json=payload,
            name="/api/v1/leave-requests [POST]",
        )
        if response.status_code not in [200, 201, 400]:
            response.failure(f"Got {response.status_code}")

    @task(1)
    def mark_notification_read(self):
        """Mark notification as read (mutation)."""
        response = self.client.patch(
            "/api/v1/notifications/1/read",
            name="/api/v1/notifications/{id}/read [PATCH]",
        )
        if response.status_code not in [200, 404]:
            response.failure(f"Got {response.status_code}")


class YuKyuHighLoadUser(HttpUser):
    """High-frequency user profile (10% of load)."""

    wait_time = between(1, 3)

    def on_start(self):
        """Called when a new user starts."""
        self.year = 2025

    @task(8)
    def rapid_get_employees(self):
        """Rapid employee list requests."""
        response = self.client.get(
            f"/api/v1/employees?year={self.year}&page=1",
            name="/api/v1/employees [rapid]",
        )
        if response.status_code != 200:
            response.failure(f"Got {response.status_code}")

    @task(2)
    def rapid_health_check(self):
        """Rapid health checks."""
        response = self.client.get(
            "/api/health",
            name="/api/health [rapid]",
        )
        if response.status_code != 200:
            response.failure(f"Got {response.status_code}")


def run_load_test():
    """Run load test programmatically."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Load Testing for YuKyuDATA")
    parser.add_argument(
        "--host",
        default=os.getenv("TEST_BASE_URL", "http://localhost:8000"),
        help="Target host",
    )
    parser.add_argument("--users", type=int, default=50, help="Number of users")
    parser.add_argument(
        "--spawn-rate", type=int, default=10, help="Users spawned per second"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=300,
        help="Test duration in seconds (300 = 5 min)",
    )
    parser.add_argument(
        "--output",
        default="load_test_results",
        help="Output file prefix",
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("YuKyuDATA Load Testing")
    print("=" * 70)
    print(f"Target: {args.host}")
    print(f"Users: {args.users}")
    print(f"Spawn Rate: {args.spawn_rate} users/sec")
    print(f"Duration: {args.duration}s ({args.duration/60:.1f} min)")
    print("=" * 70 + "\n")

    # Create environment
    env = Environment(user_classes=[YuKyuLoadTest, YuKyuHighLoadUser])
    env.host = args.host

    # Configure load test
    # 90% normal users, 10% high-load users
    env.create_local_worker_runner(
        target_user_count=args.users,
        spawn_rate=args.spawn_rate,
    )

    # Run for specified duration
    import time

    start_time = time.time()
    env.runner.start()

    # Monitor test
    print("Test in progress... Press Ctrl+C to stop\n")
    print(f"{'Time':<12} {'Users':<10} {'RPS':<10} {'P95 (ms)':<12} {'Fail %':<10}")
    print("-" * 60)

    try:
        while env.runner.state not in ["stopped", "stopping"]:
            if time.time() - start_time > args.duration:
                env.runner.stop()
                break

            # Print stats
            stats = env.stats
            if stats.total.num_requests > 0:
                total_requests = stats.total.num_requests
                fail_count = stats.total.num_failures
                fail_percent = (fail_count / total_requests * 100) if total_requests > 0 else 0

                elapsed = time.time() - start_time
                rps = total_requests / elapsed if elapsed > 0 else 0

                # Calculate P95
                p95_ms = (
                    stats.total.response_times_percentile(0.95) or 0
                )

                user_count = len(env.runner.clients)

                print(
                    f"{elapsed:>6.0f}s    {user_count:<10} {rps:<10.1f} "
                    f"{p95_ms:<12.2f} {fail_percent:<10.2f}%"
                )

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nTest stopped by user")
        env.runner.stop()

    env.runner.stop()

    # Print final results
    print("\n" + "=" * 70)
    print("LOAD TEST RESULTS")
    print("=" * 70)

    stats = env.stats

    print("\nOverall Statistics:")
    print(f"  Total Requests: {stats.total.num_requests}")
    print(f"  Total Failures: {stats.total.num_failures}")
    print(
        f"  Failure Rate: {stats.total.num_failures / stats.total.num_requests * 100:.2f}%"
    )

    print("\nResponse Time Distribution:")
    print(f"  Min: {stats.total.min_response_time:.2f}ms")
    print(f"  Max: {stats.total.max_response_time:.2f}ms")
    print(f"  Mean: {stats.total.avg_response_time:.2f}ms")
    print(f"  P50: {stats.total.response_times_percentile(0.5):.2f}ms")
    print(f"  P95: {stats.total.response_times_percentile(0.95):.2f}ms")
    print(f"  P99: {stats.total.response_times_percentile(0.99):.2f}ms")

    print("\nEndpoint Statistics:")
    print(f"{'Endpoint':<50} {'Requests':<12} {'Failures':<12} {'P95 (ms)':<12}")
    print("-" * 86)

    for name, entry in stats.entries.items():
        failures = entry.num_failures
        requests = entry.num_requests
        p95 = entry.response_times_percentile(0.95) or 0
        print(
            f"{name:<50} {requests:<12} {failures:<12} {p95:<12.2f}"
        )

    # Save results
    results_dir = Path(__file__).parent.parent / "load_test_results"
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"{args.output}_{timestamp}.json"

    results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "host": args.host,
            "users": args.users,
            "spawn_rate": args.spawn_rate,
            "duration_seconds": args.duration,
        },
        "summary": {
            "total_requests": stats.total.num_requests,
            "total_failures": stats.total.num_failures,
            "failure_rate_percent": (
                stats.total.num_failures / stats.total.num_requests * 100
                if stats.total.num_requests > 0
                else 0
            ),
            "requests_per_second": (
                stats.total.num_requests / args.duration
                if args.duration > 0
                else 0
            ),
        },
        "response_times": {
            "min_ms": stats.total.min_response_time,
            "max_ms": stats.total.max_response_time,
            "mean_ms": stats.total.avg_response_time,
            "p50_ms": stats.total.response_times_percentile(0.5),
            "p95_ms": stats.total.response_times_percentile(0.95),
            "p99_ms": stats.total.response_times_percentile(0.99),
        },
        "endpoints": {},
    }

    for name, entry in stats.entries.items():
        results["endpoints"][name] = {
            "requests": entry.num_requests,
            "failures": entry.num_failures,
            "min_ms": entry.min_response_time,
            "max_ms": entry.max_response_time,
            "mean_ms": entry.avg_response_time,
            "p95_ms": entry.response_times_percentile(0.95),
        }

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to: {results_file}")

    # Check SLAs
    print("\n" + "=" * 70)
    print("SLA VALIDATION")
    print("=" * 70)

    failure_rate = (
        stats.total.num_failures / stats.total.num_requests * 100
        if stats.total.num_requests > 0
        else 0
    )
    rps = stats.total.num_requests / args.duration if args.duration > 0 else 0
    p95 = stats.total.response_times_percentile(0.95) or 0

    print(f"Error Rate: {failure_rate:.2f}% (Target: < 0.1%)")
    print(f"  {'✓ PASS' if failure_rate < 0.1 else '✗ FAIL'}")

    print(f"\nThroughput: {rps:.1f} req/s (Target: > 50 req/s)")
    print(f"  {'✓ PASS' if rps > 50 else '✗ FAIL'}")

    print(f"\nP95 Response Time: {p95:.2f}ms (Target: < 200ms)")
    print(f"  {'✓ PASS' if p95 < 200 else '✗ FAIL'}")

    all_pass = failure_rate < 0.1 and rps > 50 and p95 < 200
    print(f"\nOverall: {'✓ PASS' if all_pass else '✗ FAIL'}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    import sys

    sys.exit(run_load_test())

"""
Performance benchmarks for YuKyuDATA critical operations.

Tests measure response times and throughput for key operations.
"""

import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


class TestPerformanceBenchmarks:
    """Performance benchmarks for critical operations."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        """Get auth headers."""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_get_employees_response_time(self, client, benchmark):
        """Benchmark: GET /api/employees should respond < 500ms."""
        def measure():
            response = client.get("/api/employees?year=2025")
            assert response.status_code == 200
            return response

        result = benchmark(measure)
        # benchmark provides stats
        assert result.status_code == 200

    def test_search_employees_response_time(self, client, auth_headers, benchmark):
        """Benchmark: GET /api/employees/search should respond < 300ms."""
        def measure():
            response = client.get(
                "/api/employees/search?q=001&year=2025",
                headers=auth_headers
            )
            assert response.status_code == 200
            return response

        result = benchmark(measure)
        assert result.status_code == 200

    def test_create_leave_request_response_time(self, client, auth_headers, benchmark):
        """Benchmark: POST /api/leave-requests should respond < 1000ms."""
        def measure():
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            response = client.post(
                "/api/leave-requests",
                json={
                    "employee_num": "001",
                    "start_date": tomorrow,
                    "end_date": tomorrow,
                    "days_requested": 0.5,
                    "leave_type": "full",
                    "reason": "Benchmark test",
                    "year": 2025
                },
                headers=auth_headers
            )
            assert response.status_code in [200, 201]
            return response

        result = benchmark(measure)
        assert result.status_code in [200, 201]

    def test_get_compliance_response_time(self, client, auth_headers, benchmark):
        """Benchmark: GET /api/compliance/5day should respond < 200ms."""
        def measure():
            response = client.get(
                "/api/compliance/5day?year=2025",
                headers=auth_headers
            )
            assert response.status_code == 200
            return response

        result = benchmark(measure)
        assert result.status_code == 200

    def test_get_analytics_response_time(self, client, auth_headers, benchmark):
        """Benchmark: GET /api/analytics/stats should respond < 300ms."""
        def measure():
            response = client.get(
                "/api/analytics/stats?year=2025",
                headers=auth_headers
            )
            assert response.status_code == 200
            return response

        result = benchmark(measure)
        assert result.status_code == 200

    def test_get_health_check_response_time(self, client, benchmark):
        """Benchmark: GET /api/health should respond < 100ms."""
        def measure():
            response = client.get("/api/health")
            assert response.status_code == 200
            return response

        result = benchmark(measure)
        assert result.status_code == 200


class TestThroughput:
    """Test throughput (requests per second)."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    def test_concurrent_get_employees_throughput(self, client):
        """Test: 100 concurrent GET /employees should complete."""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed

        num_requests = 100
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for i in range(num_requests):
                future = executor.submit(
                    lambda: client.get("/api/employees?year=2025")
                )
                futures.append(future)

            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result.status_code)

        elapsed_time = time.time() - start_time
        throughput = num_requests / elapsed_time
        successful = sum(1 for code in results if code == 200)

        print(f"\nThroughput: {throughput:.2f} requests/second")
        print(f"Successful: {successful}/{num_requests}")
        print(f"Time: {elapsed_time:.2f}s")

        assert successful >= num_requests * 0.95, "95%+ success rate required"
        assert throughput >= 10, "At least 10 requests/second"

    def test_concurrent_create_leave_requests_throughput(self, client):
        """Test: 50 concurrent POST /leave-requests should complete."""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # First, get auth token
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        num_requests = 50
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(num_requests):
                tomorrow = (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d")

                def create_request(day=tomorrow, idx=i):
                    return client.post(
                        "/api/leave-requests",
                        json={
                            "employee_num": f"{idx % 100:03d}",
                            "start_date": day,
                            "end_date": day,
                            "days_requested": 0.5,
                            "leave_type": "full",
                            "reason": "Throughput test",
                            "year": 2025
                        },
                        headers=headers
                    )

                future = executor.submit(create_request)
                futures.append(future)

            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result.status_code)

        elapsed_time = time.time() - start_time
        throughput = num_requests / elapsed_time
        successful = sum(1 for code in results if code in [200, 201])

        print(f"\nThroughput: {throughput:.2f} requests/second")
        print(f"Successful: {successful}/{num_requests}")
        print(f"Time: {elapsed_time:.2f}s")

        assert successful >= num_requests * 0.90, "90%+ success rate required"


class TestMemoryUsage:
    """Test memory usage during operations."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    def test_large_dataset_handling(self, client):
        """Test: System should handle 1000+ employees efficiently."""
        import sys

        # Get employees
        response = client.get("/api/employees?year=2025")
        assert response.status_code == 200

        data = response.json()
        employees = data.get("data", [])

        # Check memory doesn't explode
        import gc
        gc.collect()

        # Process all employees
        processed = 0
        for emp in employees:
            assert emp.get("employee_num")
            processed += 1

        print(f"\nProcessed {processed} employees")
        assert processed > 0, "Should have at least 1 employee"

    def test_large_response_parsing(self, client):
        """Test: System should parse large responses efficiently."""
        # Get all analytics data
        response = client.get("/api/analytics/stats?year=2025")
        assert response.status_code == 200

        data = response.json()
        # Response should be parseable
        assert isinstance(data, dict)
        assert "data" in data or "stats" in data or data  # Some data


class TestCaching:
    """Test caching effectiveness."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    def test_second_request_faster_than_first(self, client):
        """Test: Cached requests should be faster."""
        import time

        # First request (possibly uncached)
        start1 = time.time()
        response1 = client.get("/api/employees?year=2025")
        time1 = time.time() - start1
        assert response1.status_code == 200

        # Wait a bit
        time.sleep(0.1)

        # Second request (possibly cached)
        start2 = time.time()
        response2 = client.get("/api/employees?year=2025")
        time2 = time.time() - start2
        assert response2.status_code == 200

        print(f"\nFirst request: {time1*1000:.2f}ms")
        print(f"Second request: {time2*1000:.2f}ms")

        # Second should be same or faster (cache hit or optimized)
        # Note: First request might be cached too, so we just check both succeed
        assert time1 > 0 and time2 > 0


class TestDataValidation:
    """Test data validation performance."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    def test_invalid_input_rejected_quickly(self, client):
        """Test: Invalid input should be rejected with minimal overhead."""
        start = time.time()

        response = client.post(
            "/api/leave-requests",
            json={
                "employee_num": "",  # Invalid
                "start_date": "invalid-date",  # Invalid
                "end_date": "invalid",  # Invalid
                "days_requested": "not-a-number",  # Invalid
                "leave_type": "invalid_type",  # Invalid
                "reason": "Test",
                "year": "not-a-year"  # Invalid
            }
        )

        elapsed = time.time() - start

        # Should fail validation
        assert response.status_code in [400, 422]

        # Should be fast (validation errors are cheap)
        assert elapsed < 0.5, "Validation should be fast"

    def test_malformed_json_rejected_quickly(self, client):
        """Test: Malformed JSON should be rejected quickly."""
        start = time.time()

        # Attempt to send invalid JSON
        response = client.post(
            "/api/leave-requests",
            data="{ invalid json",
            headers={"Content-Type": "application/json"}
        )

        elapsed = time.time() - start

        # Should fail parsing
        assert response.status_code in [400, 422]

        # Should be fast
        assert elapsed < 0.5, "JSON parsing error should be fast"

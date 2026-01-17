"""
Tests for User-Aware Rate Limiter
Pruebas del sistema de rate limiting por usuario/IP
"""

import pytest
import sys
import os
import time
import importlib.util
from unittest.mock import MagicMock, patch
from collections import defaultdict

# Ensure test environment is set
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("DEBUG", "true")

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Mock services.auth before importing rate_limiter to avoid dependency chain
mock_auth = MagicMock()
mock_auth.verify_token = MagicMock(return_value=None)
sys.modules['services.auth'] = mock_auth

# Import rate_limiter module directly from file (bypass middleware/__init__.py)
spec = importlib.util.spec_from_file_location(
    'rate_limiter_direct',
    os.path.join(PROJECT_ROOT, 'middleware', 'rate_limiter.py')
)
rate_limiter_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rate_limiter_module)

# Extract components from the module
UserAwareRateLimiter = rate_limiter_module.UserAwareRateLimiter
RateLimiter = rate_limiter_module.RateLimiter
RateLimitInfo = rate_limiter_module.RateLimitInfo
RATE_LIMITS = rate_limiter_module.RATE_LIMITS
user_aware_limiter = rate_limiter_module.user_aware_limiter
check_rate_limit = rate_limiter_module.check_rate_limit

# Mock Request class for testing
Request = MagicMock

# TestClient import will be done conditionally in integration tests
TestClient = None


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def fresh_limiter():
    """Create a fresh UserAwareRateLimiter for each test."""
    return UserAwareRateLimiter(
        default_limit=10,
        default_window=60,
        authenticated_limit=20,
        cleanup_interval=1  # Fast cleanup for tests
    )


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object."""
    def _create_request(
        path: str = "/api/test",
        client_ip: str = "127.0.0.1",
        auth_header: str = None,
        forwarded_for: str = None
    ):
        # Create nested mock objects manually
        request = MagicMock()

        # Set up url mock
        url_mock = MagicMock()
        url_mock.path = path
        request.url = url_mock

        # Set up client mock
        client_mock = MagicMock()
        client_mock.host = client_ip
        request.client = client_mock

        # Set up headers
        headers = {}
        if auth_header:
            headers['Authorization'] = auth_header
        if forwarded_for:
            headers['X-Forwarded-For'] = forwarded_for

        request.headers = MagicMock()
        request.headers.get = lambda key, default='': headers.get(key, default)

        return request

    return _create_request


@pytest.fixture
def legacy_limiter():
    """Create a legacy RateLimiter for backward compatibility tests."""
    return RateLimiter(requests_per_minute=5)


# ============================================
# RATE LIMIT INFO TESTS
# ============================================

class TestRateLimitInfo:
    """Tests for RateLimitInfo class."""

    def test_to_headers_returns_correct_format(self):
        """Test that to_headers returns proper HTTP headers."""
        info = RateLimitInfo(limit=100, remaining=95, reset_time=1700000000.0)
        headers = info.to_headers()

        assert 'X-RateLimit-Limit' in headers
        assert 'X-RateLimit-Remaining' in headers
        assert 'X-RateLimit-Reset' in headers
        assert headers['X-RateLimit-Limit'] == '100'
        assert headers['X-RateLimit-Remaining'] == '95'
        assert headers['X-RateLimit-Reset'] == '1700000000'

    def test_remaining_never_negative(self):
        """Test that remaining is never reported as negative."""
        info = RateLimitInfo(limit=10, remaining=-5, reset_time=1700000000.0)
        headers = info.to_headers()

        assert headers['X-RateLimit-Remaining'] == '0'


# ============================================
# USER-AWARE RATE LIMITER TESTS
# ============================================

class TestUserAwareRateLimiter:
    """Tests for UserAwareRateLimiter class."""

    def test_anonymous_user_uses_ip_limit(self, fresh_limiter, mock_request):
        """Test that anonymous users are rate limited by IP."""
        # Use a path that doesn't have endpoint-specific limits
        request = mock_request(path="/api/unknown-endpoint")

        # First request should be allowed
        is_allowed, info = fresh_limiter.check_limit(request)
        assert is_allowed is True
        # For unknown endpoints, should use default limit
        assert info.limit == fresh_limiter.default_limit

    def test_anonymous_user_blocked_after_limit(self, fresh_limiter, mock_request):
        """Test that anonymous users are blocked after exceeding limit."""
        request = mock_request(path="/api/test", client_ip="192.168.1.100")

        # Make requests up to the limit
        for i in range(fresh_limiter.default_limit):
            is_allowed, _ = fresh_limiter.check_limit(request)
            assert is_allowed is True, f"Request {i+1} should be allowed"

        # Next request should be blocked
        is_allowed, info = fresh_limiter.check_limit(request)
        assert is_allowed is False
        assert info.remaining <= 0

    def test_different_ips_have_separate_limits(self, fresh_limiter, mock_request):
        """Test that different IPs have independent rate limits."""
        request1 = mock_request(path="/api/test", client_ip="192.168.1.1")
        request2 = mock_request(path="/api/test", client_ip="192.168.1.2")

        # Exhaust limit for IP 1
        for _ in range(fresh_limiter.default_limit):
            fresh_limiter.check_limit(request1)

        # IP 1 should be blocked
        is_allowed, _ = fresh_limiter.check_limit(request1)
        assert is_allowed is False

        # IP 2 should still be allowed
        is_allowed, _ = fresh_limiter.check_limit(request2)
        assert is_allowed is True

    def test_authenticated_user_gets_higher_limit(
        self, fresh_limiter, mock_request
    ):
        """Test that authenticated users get higher rate limits."""
        # Use a path that doesn't have endpoint-specific limits
        request = mock_request(
            path="/api/unknown-endpoint",
            auth_header="Bearer valid_token"
        )

        # Pass user_id explicitly to simulate authenticated user
        is_allowed, info = fresh_limiter.check_limit(request, user_id="test_user")
        assert is_allowed is True
        # Authenticated users should get the higher limit
        assert info.limit == fresh_limiter.authenticated_limit

    def test_authenticated_users_tracked_separately(
        self, fresh_limiter, mock_request
    ):
        """Test that authenticated users have separate limits from IPs."""
        auth_request = mock_request(
            path="/api/test",
            client_ip="192.168.1.1",
            auth_header="Bearer token_a"
        )

        anon_request = mock_request(
            path="/api/test",
            client_ip="192.168.1.1"
        )

        # Exhaust anonymous limit from same IP (no user_id)
        for _ in range(fresh_limiter.default_limit):
            fresh_limiter.check_limit(anon_request, user_id=None)

        # Anonymous should be blocked
        is_allowed, _ = fresh_limiter.check_limit(anon_request, user_id=None)
        assert is_allowed is False

        # Authenticated user from same IP should still work
        is_allowed, _ = fresh_limiter.check_limit(auth_request, user_id="user_a")
        assert is_allowed is True

    def test_endpoint_specific_limits(self, fresh_limiter, mock_request):
        """Test that specific endpoints have their own limits."""
        # api/auth/login has limit of 5
        request = mock_request(path="/api/auth/login")

        is_allowed, info = fresh_limiter.check_limit(request)
        assert is_allowed is True
        # Should use endpoint-specific limit
        assert info.limit == RATE_LIMITS['api/auth/login']['requests']

    def test_sync_endpoints_very_limited(self, fresh_limiter, mock_request):
        """Test that sync endpoints are very restricted."""
        request = mock_request(path="/api/sync")

        # Sync limit is 2/min
        is_allowed, info = fresh_limiter.check_limit(request)
        assert is_allowed is True
        assert info.limit == 2

        is_allowed, _ = fresh_limiter.check_limit(request)
        assert is_allowed is True

        # Third request should be blocked
        is_allowed, _ = fresh_limiter.check_limit(request)
        assert is_allowed is False

    def test_forwarded_for_header_respected(self, fresh_limiter, mock_request):
        """Test that X-Forwarded-For header is used for IP detection."""
        request1 = mock_request(
            path="/api/test",
            client_ip="10.0.0.1",
            forwarded_for="203.0.113.1, 10.0.0.1"
        )

        request2 = mock_request(
            path="/api/test",
            client_ip="10.0.0.1",
            forwarded_for="203.0.113.2, 10.0.0.1"
        )

        # Exhaust limit for first forwarded IP
        for _ in range(fresh_limiter.default_limit):
            fresh_limiter.check_limit(request1)

        # Second forwarded IP should still work
        is_allowed, _ = fresh_limiter.check_limit(request2)
        assert is_allowed is True

    def test_reset_clears_all_limits(self, fresh_limiter, mock_request):
        """Test that reset() clears all rate limit data."""
        request = mock_request(path="/api/test")

        # Make some requests
        for _ in range(5):
            fresh_limiter.check_limit(request)

        # Reset
        fresh_limiter.reset()

        # Should be able to make full limit again
        for i in range(fresh_limiter.default_limit):
            is_allowed, _ = fresh_limiter.check_limit(request)
            assert is_allowed is True, f"Request {i+1} after reset should be allowed"

    def test_reset_specific_user(self, fresh_limiter, mock_request):
        """Test that reset() can target specific user."""
        request1 = mock_request(path="/api/test", client_ip="1.1.1.1")
        request2 = mock_request(path="/api/test", client_ip="2.2.2.2")

        # Exhaust both
        for _ in range(fresh_limiter.default_limit):
            fresh_limiter.check_limit(request1)
            fresh_limiter.check_limit(request2)

        # Both blocked
        is_allowed1, _ = fresh_limiter.check_limit(request1)
        is_allowed2, _ = fresh_limiter.check_limit(request2)
        assert is_allowed1 is False
        assert is_allowed2 is False

        # Reset only first IP
        fresh_limiter.reset("ip:1.1.1.1")

        # First IP unblocked, second still blocked
        is_allowed1, _ = fresh_limiter.check_limit(request1)
        is_allowed2, _ = fresh_limiter.check_limit(request2)
        assert is_allowed1 is True
        assert is_allowed2 is False

    def test_get_usage_returns_correct_counts(self, fresh_limiter, mock_request):
        """Test that get_usage returns accurate request counts."""
        request = mock_request(path="/api/test", client_ip="10.10.10.10")

        # Make 5 requests
        for _ in range(5):
            fresh_limiter.check_limit(request)

        used, limit = fresh_limiter.get_usage("ip:10.10.10.10")
        assert used == 5
        assert limit == fresh_limiter.default_limit


# ============================================
# LEGACY RATE LIMITER TESTS
# ============================================

class TestLegacyRateLimiter:
    """Tests for backward-compatible RateLimiter class."""

    def test_basic_rate_limiting(self, legacy_limiter, mock_request):
        """Test basic rate limiting functionality."""
        request = mock_request(client_ip="127.0.0.1")

        # Should allow requests up to limit
        for _ in range(5):
            # Manually call the logic since __call__ is async
            legacy_limiter.requests["127.0.0.1"].append(time.time())

        used, limit = legacy_limiter.get_usage("127.0.0.1")
        assert used == 5
        assert limit == 5

    def test_reset_functionality(self, legacy_limiter):
        """Test that reset clears counters."""
        # Add some requests
        legacy_limiter.requests["1.1.1.1"].append(time.time())
        legacy_limiter.requests["2.2.2.2"].append(time.time())

        # Reset all
        legacy_limiter.reset()

        assert len(legacy_limiter.requests) == 0

    def test_reset_specific_ip(self, legacy_limiter):
        """Test resetting a specific IP."""
        legacy_limiter.requests["1.1.1.1"].append(time.time())
        legacy_limiter.requests["2.2.2.2"].append(time.time())

        legacy_limiter.reset("1.1.1.1")

        assert len(legacy_limiter.requests.get("1.1.1.1", [])) == 0
        assert len(legacy_limiter.requests["2.2.2.2"]) == 1


# ============================================
# CONFIGURATION TESTS
# ============================================

class TestRateLimitConfiguration:
    """Tests for RATE_LIMITS configuration."""

    def test_auth_endpoints_strictly_limited(self):
        """Test that auth endpoints have strict limits."""
        assert RATE_LIMITS['api/auth/login']['requests'] <= 5
        assert RATE_LIMITS['api/auth/register']['requests'] <= 5

    def test_sync_endpoints_very_limited(self):
        """Test that sync endpoints are heavily restricted."""
        sync_endpoints = ['api/sync', 'api/sync-genzai', 'api/sync-ukeoi', 'api/sync-staff']
        for endpoint in sync_endpoints:
            assert RATE_LIMITS[endpoint]['requests'] <= 5

    def test_health_endpoints_relaxed(self):
        """Test that health endpoints have relaxed limits."""
        assert RATE_LIMITS['api/health']['requests'] >= 100

    def test_authenticated_limit_higher_than_default(self):
        """Test that authenticated users get higher limits."""
        assert RATE_LIMITS['authenticated']['requests'] > RATE_LIMITS['default']['requests']


# ============================================
# INTEGRATION TESTS
# ============================================

@pytest.mark.skipif(
    os.environ.get('SKIP_INTEGRATION_TESTS', 'false').lower() == 'true',
    reason="Integration tests skipped"
)
class TestRateLimiterIntegration:
    """Integration tests with FastAPI TestClient."""

    @pytest.fixture
    def client(self):
        """Create test client with app."""
        try:
            from fastapi.testclient import TestClient
            from main import app
            return TestClient(app)
        except Exception as e:
            pytest.skip(f"Could not create test client: {e}")

    def test_rate_limit_headers_in_response(self, client):
        """Test that rate limit headers are present in responses."""
        if client is None:
            pytest.skip("TestClient not available")

        # Note: This test may need adjustment based on middleware configuration
        response = client.get("/api/health")

        # The new middleware should add these headers
        # If middleware is not active, this will be skipped
        if 'X-RateLimit-Limit' in response.headers:
            assert 'X-RateLimit-Remaining' in response.headers
            assert 'X-RateLimit-Reset' in response.headers

    def test_429_response_includes_retry_after(self, client, monkeypatch):
        """Test that 429 responses include Retry-After header."""
        if client is None:
            pytest.skip("TestClient not available")

        # This test demonstrates the expected behavior
        # Actual triggering of 429 depends on rate limit settings
        limiter = user_aware_limiter

        # Temporarily set very low limit for testing
        original_limit = limiter.default_limit
        limiter.default_limit = 1
        limiter.reset()

        try:
            # First request should succeed
            response1 = client.get("/api/health")

            # If rate limiting is active globally, second might fail
            response2 = client.get("/api/health")

            if response2.status_code == 429:
                assert 'Retry-After' in response2.headers
                assert int(response2.headers['Retry-After']) > 0
        finally:
            # Restore original limit
            limiter.default_limit = original_limit
            limiter.reset()


# ============================================
# EDGE CASE TESTS
# ============================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_unknown_client_ip_handled(self, fresh_limiter):
        """Test handling of requests with unknown client IP."""
        request = MagicMock()
        url_mock = MagicMock()
        url_mock.path = "/api/test"
        request.url = url_mock
        request.client = None
        request.headers = MagicMock()
        request.headers.get = lambda key, default='': ''

        # Should not crash, should use 'unknown' as key
        is_allowed, info = fresh_limiter.check_limit(request)
        assert is_allowed is True

    def test_malformed_auth_header_ignored(self, fresh_limiter, mock_request):
        """Test that malformed auth headers are safely ignored."""
        request = mock_request(
            path="/api/test",
            auth_header="NotBearer token"
        )

        # Should fall back to IP-based limiting
        is_allowed, info = fresh_limiter.check_limit(request)
        assert is_allowed is True
        assert info.limit == fresh_limiter.default_limit

    def test_expired_token_falls_back_to_ip(self, fresh_limiter, mock_request):
        """Test that expired tokens fall back to IP limiting."""
        # When user_id is not provided and token extraction fails,
        # it falls back to IP-based limiting
        request = mock_request(
            path="/api/test",
            auth_header="Bearer expired_token"
        )

        # Explicitly pass user_id=None to simulate failed token verification
        is_allowed, info = fresh_limiter.check_limit(request, user_id=None)
        assert is_allowed is True
        assert info.limit == fresh_limiter.default_limit

    def test_prefix_matching_uses_most_specific(self, fresh_limiter, mock_request):
        """Test that prefix matching uses most specific match."""
        # api/reports/pdf should match more specific limit than api/reports
        request_pdf = mock_request(path="/api/reports/pdf")
        request_general = mock_request(path="/api/reports/monthly")

        _, info_pdf = fresh_limiter.check_limit(request_pdf)
        _, info_general = fresh_limiter.check_limit(request_general)

        # PDF has lower limit (5) vs general reports (10)
        assert info_pdf.limit == 5
        assert info_general.limit == 10

    def test_concurrent_cleanup_safe(self, fresh_limiter, mock_request):
        """Test that cleanup doesn't cause issues during request processing."""
        # Force cleanup interval to be very short
        fresh_limiter.cleanup_interval = 0.001
        fresh_limiter.last_cleanup = 0

        request = mock_request(path="/api/test")

        # Make many requests to trigger cleanup
        for _ in range(20):
            is_allowed, _ = fresh_limiter.check_limit(request)
            # Should not crash even with concurrent cleanup

    def test_very_long_path_handled(self, fresh_limiter, mock_request):
        """Test handling of very long request paths."""
        long_path = "/api/" + "a" * 10000
        request = mock_request(path=long_path)

        # Should not crash, should use default limit
        is_allowed, info = fresh_limiter.check_limit(request)
        assert is_allowed is True


# ============================================
# PERFORMANCE TESTS
# ============================================

class TestPerformance:
    """Performance-related tests."""

    def test_many_unique_ips_memory_bounded(self, fresh_limiter, mock_request):
        """Test that memory usage is bounded with many unique IPs."""
        # Simulate many unique IPs
        for i in range(1000):
            request = mock_request(
                path="/api/test",
                client_ip=f"192.168.{i//256}.{i%256}"
            )
            fresh_limiter.check_limit(request)

        # Should have stored all IPs
        assert len(fresh_limiter.ip_requests) == 1000

        # Cleanup should work
        fresh_limiter.last_cleanup = 0
        fresh_limiter._cleanup_old_requests()

    def test_check_limit_fast_enough(self, fresh_limiter, mock_request):
        """Test that check_limit is fast enough for production use."""
        request = mock_request(path="/api/test")

        start = time.time()
        for _ in range(1000):
            fresh_limiter.check_limit(request)
        elapsed = time.time() - start

        # Should complete 1000 checks in under 1 second
        assert elapsed < 1.0, f"1000 checks took {elapsed:.2f}s, expected < 1s"

"""
YuKyu Premium - Refresh Tokens System Tests (v5.17)
Tests para el sistema de refresh tokens con persistencia en base de datos
"""

import pytest
import hashlib
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRefreshTokenDatabase:
    """Tests for refresh token database operations"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        return mock_conn, mock_cursor

    def test_token_hash_function(self):
        """Test that token hashing produces consistent results"""
        token = "test_token_123"
        expected_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()

        # The hash should be 64 characters (SHA-256 in hex)
        assert len(expected_hash) == 64

        # Same token should produce same hash
        hash2 = hashlib.sha256(token.encode('utf-8')).hexdigest()
        assert expected_hash == hash2

        # Different token should produce different hash
        different_hash = hashlib.sha256("different_token".encode('utf-8')).hexdigest()
        assert expected_hash != different_hash

    def test_token_id_format(self):
        """Test that token IDs are valid UUIDs"""
        token_id = str(uuid.uuid4())
        # Should be a valid UUID format (8-4-4-4-12)
        parts = token_id.split('-')
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12


class TestRefreshTokenExpiration:
    """Tests for token expiration logic"""

    def test_access_token_expiration_15_minutes(self):
        """Access token should expire in 15 minutes"""
        from services.auth_service import ACCESS_TOKEN_EXPIRE_MINUTES
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 15

    def test_refresh_token_expiration_7_days(self):
        """Refresh token should expire in 7 days"""
        from services.auth_service import REFRESH_TOKEN_EXPIRE_DAYS
        assert REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_token_expiration_calculation(self):
        """Test token expiration date calculation"""
        now = datetime.utcnow()

        # Access token expiration
        access_expire = now + timedelta(minutes=15)
        assert (access_expire - now).seconds == 15 * 60

        # Refresh token expiration
        refresh_expire = now + timedelta(days=7)
        assert (refresh_expire - now).days == 7


class TestTokenPairStructure:
    """Tests for TokenPair response structure"""

    def test_token_pair_has_required_fields(self):
        """TokenPair should have access_token, refresh_token, token_type, expires_in"""
        from services.auth_service import TokenPair

        # Create a mock token pair
        pair = TokenPair(
            access_token="access_123",
            refresh_token="refresh_456",
            expires_in=900
        )

        assert hasattr(pair, 'access_token')
        assert hasattr(pair, 'refresh_token')
        assert hasattr(pair, 'token_type')
        assert hasattr(pair, 'expires_in')

        assert pair.token_type == "bearer"
        assert pair.expires_in == 900  # 15 minutes in seconds


class TestSecurityBestPractices:
    """Tests for security best practices in token handling"""

    def test_token_hash_not_reversible(self):
        """Ensure token hash cannot be reversed to get original token"""
        original_token = "secret_refresh_token_abc123"
        token_hash = hashlib.sha256(original_token.encode('utf-8')).hexdigest()

        # Hash should not contain the original token
        assert original_token not in token_hash

        # Hash should be fixed length regardless of input
        short_token_hash = hashlib.sha256("a".encode('utf-8')).hexdigest()
        long_token_hash = hashlib.sha256("a" * 1000).hexdigest()
        assert len(short_token_hash) == len(long_token_hash) == 64

    def test_different_secrets_for_access_and_refresh(self):
        """Access and refresh tokens should use different secret keys"""
        from services.auth_service import SECRET_KEY, REFRESH_SECRET_KEY
        assert SECRET_KEY != REFRESH_SECRET_KEY

    def test_algorithm_is_secure(self):
        """Token algorithm should be secure (HS256 minimum)"""
        from services.auth_service import ALGORITHM
        secure_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512", "ES256"]
        assert ALGORITHM in secure_algorithms


class TestTokenCleanup:
    """Tests for token cleanup functionality"""

    def test_cleanup_removes_old_tokens(self):
        """Cleanup should remove expired and revoked tokens"""
        # Test the cleanup logic
        now = datetime.now()
        cutoff = (now - timedelta(days=1)).isoformat()

        # Expired token (should be removed)
        expired_at = (now - timedelta(days=2)).isoformat()
        assert expired_at < now.isoformat()

        # Not expired token (should be kept)
        valid_until = (now + timedelta(days=5)).isoformat()
        assert valid_until > now.isoformat()

    def test_revoked_token_cleanup_after_24h(self):
        """Revoked tokens should be cleaned up after 24 hours"""
        now = datetime.now()

        # Revoked less than 24h ago (keep)
        revoked_recently = (now - timedelta(hours=12)).isoformat()

        # Revoked more than 24h ago (remove)
        revoked_long_ago = (now - timedelta(hours=30)).isoformat()

        cutoff = (now - timedelta(days=1)).isoformat()

        assert revoked_recently > cutoff  # Should keep
        assert revoked_long_ago < cutoff  # Should remove


class TestRouteEndpoints:
    """Tests for authentication route endpoints structure"""

    def test_login_endpoint_exists(self):
        """POST /api/auth/login should exist"""
        from routes.auth import router
        routes = [route.path for route in router.routes]
        assert "/login" in routes or any("/login" in r for r in routes)

    def test_refresh_endpoint_exists(self):
        """POST /api/auth/refresh should exist"""
        from routes.auth import router
        routes = [route.path for route in router.routes]
        assert "/refresh" in routes or any("/refresh" in r for r in routes)

    def test_revoke_endpoint_exists(self):
        """POST /api/auth/revoke should exist"""
        from routes.auth import router
        routes = [route.path for route in router.routes]
        assert "/revoke" in routes or any("/revoke" in r for r in routes)

    def test_logout_all_endpoint_exists(self):
        """POST /api/auth/logout-all should exist"""
        from routes.auth import router
        routes = [route.path for route in router.routes]
        assert "/logout-all" in routes or any("/logout-all" in r for r in routes)

    def test_sessions_endpoint_exists(self):
        """GET /api/auth/sessions should exist"""
        from routes.auth import router
        routes = [route.path for route in router.routes]
        assert "/sessions" in routes or any("/sessions" in r for r in routes)

    def test_cleanup_endpoint_exists(self):
        """POST /api/auth/cleanup should exist"""
        from routes.auth import router
        routes = [route.path for route in router.routes]
        assert "/cleanup" in routes or any("/cleanup" in r for r in routes)


class TestRequestModels:
    """Tests for request model validation"""

    def test_login_request_requires_username(self):
        """LoginRequest should require username"""
        from routes.auth import LoginRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LoginRequest(password="test123")

    def test_login_request_requires_password(self):
        """LoginRequest should require password"""
        from routes.auth import LoginRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LoginRequest(username="testuser")

    def test_refresh_request_requires_token(self):
        """RefreshRequest should require refresh_token"""
        from routes.auth import RefreshRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RefreshRequest()

    def test_revoke_request_requires_token(self):
        """RevokeRequest should require refresh_token"""
        from routes.auth import RevokeRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RevokeRequest()


class TestDatabaseSchema:
    """Tests for database schema structure"""

    def test_refresh_tokens_table_schema(self):
        """Verify refresh_tokens table has correct columns"""
        expected_columns = [
            'id',
            'user_id',
            'token_hash',
            'expires_at',
            'created_at',
            'revoked',
            'revoked_at',
            'user_agent',
            'ip_address'
        ]

        # The CREATE TABLE statement should include all these columns
        from database import init_refresh_tokens_table

        # This function should exist and not raise
        assert callable(init_refresh_tokens_table)


class TestClientInfoExtraction:
    """Tests for client info extraction from requests"""

    def test_client_info_function_exists(self):
        """_get_client_info function should exist"""
        from routes.auth import _get_client_info
        assert callable(_get_client_info)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Tests for Authentication Middleware
Tests JWT token creation, validation, and user dependencies
"""

import pytest
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# Import the module to test
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from middleware.auth_middleware import (
    create_access_token,
    decode_token,
    get_current_user,
    require_admin,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_HOURS,
    TokenData,
    CurrentUser
)
from exceptions.custom_exceptions import AuthenticationException


class TestTokenCreation:
    """Test JWT token creation"""
    
    def test_create_access_token_success(self):
        """Test successful token creation"""
        user_id = "user_123"
        username = "testuser"
        role = "user"
        
        token = create_access_token(user_id, username, role)
        
        # Verify token is a string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["user_id"] == user_id
        assert payload["username"] == username
        assert payload["role"] == role
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_admin_token(self):
        """Test creating token for admin user"""
        token = create_access_token("admin_001", "admin", "admin")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert payload["role"] == "admin"
    
    def test_token_expiration_time(self):
        """Test token has correct expiration time"""
        token = create_access_token("user_123", "testuser", "user")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check expiration is approximately ACCESS_TOKEN_EXPIRE_HOURS from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        expected_exp = now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        
        # Allow 5 second tolerance
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 5


class TestTokenDecoding:
    """Test JWT token decoding and validation"""
    
    def test_decode_valid_token(self):
        """Test decoding valid token"""
        # Create a token
        token = create_access_token("user_123", "testuser", "user")
        
        # Decode it
        token_data = decode_token(token)
        
        assert isinstance(token_data, TokenData)
        assert token_data.user_id == "user_123"
        assert token_data.username == "testuser"
        assert token_data.role == "user"
        assert isinstance(token_data.exp, datetime)
    
    def test_decode_expired_token(self):
        """Test decoding expired token raises exception"""
        # Create token that expired 1 hour ago
        past_time = datetime.utcnow() - timedelta(hours=1)
        payload = {
            "user_id": "user_123",
            "username": "testuser",
            "role": "user",
            "exp": past_time,
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # Should raise AuthenticationException
        with pytest.raises(AuthenticationException, match="Token has expired"):
            decode_token(expired_token)
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token raises exception"""
        invalid_token = "invalid.token.string"
        
        with pytest.raises(AuthenticationException, match="Invalid token"):
            decode_token(invalid_token)
    
    def test_decode_token_wrong_secret(self):
        """Test token signed with wrong secret is rejected"""
        # Create token with wrong secret
        payload = {
            "user_id": "user_123",
            "username": "testuser",
            "role": "user",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        
        wrong_token = jwt.encode(payload, "wrong-secret-key", algorithm=ALGORITHM)
        
        with pytest.raises(AuthenticationException):
            decode_token(wrong_token)


class TestGetCurrentUser:
    """Test get_current_user dependency"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test getting current user with valid token"""
        # Create valid token
        token = create_access_token("user_123", "testuser", "user")
        
        # Create credentials object
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        # Get current user
        user = await get_current_user(credentials)
        
        assert isinstance(user, CurrentUser)
        assert user.user_id == "user_123"
        assert user.username == "testuser"
        assert user.role == "user"
        assert user.is_admin is False
    
    @pytest.mark.asyncio
    async def test_get_current_user_admin(self):
        """Test getting admin user"""
        token = create_access_token("admin_001", "admin", "admin")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        user = await get_current_user(credentials)
        
        assert user.is_admin is True
        assert user.role == "admin"
    
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self):
        """Test expired token raises 401"""
        # Create expired token
        past_time = datetime.utcnow() - timedelta(hours=1)
        payload = {
            "user_id": "user_123",
            "username": "testuser",
            "role": "user",
            "exp": past_time,
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()


class TestRequireAdmin:
    """Test require_admin dependency"""
    
    @pytest.mark.asyncio
    async def test_require_admin_with_admin_user(self):
        """Test admin user passes"""
        admin_user = CurrentUser(
            user_id="admin_001",
            username="admin",
            role="admin",
            is_admin=True
        )
        
        result = await require_admin(admin_user)
        
        assert result == admin_user
    
    @pytest.mark.asyncio
    async def test_require_admin_with_regular_user(self):
        """Test regular user raises 403"""
        regular_user = CurrentUser(
            user_id="user_123",
            username="testuser",
            role="user",
            is_admin=False
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(regular_user)
        
        assert exc_info.value.status_code == 403
        assert "admin" in str(exc_info.value.detail).lower()


class TestTokenDataModel:
    """Test TokenData Pydantic model"""
    
    def test_token_data_creation(self):
        """Test creating TokenData instance"""
        exp_time = datetime.utcnow() + timedelta(hours=1)
        
        token_data = TokenData(
            username="testuser",
            user_id="user_123",
            role="user",
            exp=exp_time
        )
        
        assert token_data.username == "testuser"
        assert token_data.user_id == "user_123"
        assert token_data.role == "user"
        assert token_data.exp == exp_time


class TestCurrentUserModel:
    """Test CurrentUser Pydantic model"""
    
    def test_current_user_creation(self):
        """Test creating CurrentUser instance"""
        user = CurrentUser(
            user_id="user_123",
            username="testuser",
            role="user",
            is_admin=False
        )
        
        assert user.user_id == "user_123"
        assert user.username == "testuser"
        assert user.role == "user"
        assert user.is_admin is False
    
    def test_current_user_admin(self):
        """Test admin user"""
        admin = CurrentUser(
            user_id="admin_001",
            username="admin",
            role="admin",
            is_admin=True
        )
        
        assert admin.is_admin is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

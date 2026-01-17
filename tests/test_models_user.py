"""
Tests para models/user.py - Modelos de usuarios y autenticacion
Tests completos para LoginRequest, TokenResponse, etc.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
import json

from models.user import (
    UserRole,
    UserLogin,
    LoginRequest,
    RefreshRequest,
    RevokeRequest,
    UserBase,
    UserCreate,
    RegisterRequest,
    UserUpdate,
    UserResponse,
    ChangePasswordRequest,
    ResetPasswordRequest,
    SetPasswordRequest,
    TokenResponse,
    TokenPair,
    TokenData,
    CurrentUser,
)


# ============================================
# Enum Tests
# ============================================

class TestUserRole:
    """Tests para el enum UserRole."""

    def test_admin_role(self):
        """Test rol admin."""
        assert UserRole.ADMIN.value == "admin"

    def test_manager_role(self):
        """Test rol manager."""
        assert UserRole.MANAGER.value == "manager"

    def test_user_role(self):
        """Test rol user."""
        assert UserRole.USER.value == "user"

    def test_readonly_role(self):
        """Test rol readonly."""
        assert UserRole.READONLY.value == "readonly"

    def test_all_roles(self):
        """Test todos los roles."""
        roles = [r.value for r in UserRole]
        assert len(roles) == 4
        assert "admin" in roles
        assert "readonly" in roles


# ============================================
# UserLogin Tests
# ============================================

class TestUserLogin:
    """Tests para el modelo UserLogin."""

    def test_valid_login(self):
        """Test login valido."""
        login = UserLogin(
            username="admin",
            password="password123"
        )
        assert login.username == "admin"
        assert login.password == "password123"

    def test_username_constraints(self):
        """Test constraints del username."""
        # Vacio
        with pytest.raises(ValidationError):
            UserLogin(username="", password="password123")

        # Muy largo
        with pytest.raises(ValidationError):
            UserLogin(username="a" * 101, password="password123")

    def test_password_min_length(self):
        """Test longitud minima de password."""
        with pytest.raises(ValidationError):
            UserLogin(username="admin", password="short")

        # Exactamente 8 caracteres (minimo)
        login = UserLogin(username="admin", password="12345678")
        assert len(login.password) == 8

    def test_password_max_length(self):
        """Test longitud maxima de password."""
        with pytest.raises(ValidationError):
            UserLogin(username="admin", password="a" * 256)

    def test_japanese_username(self):
        """Test username japones."""
        login = UserLogin(
            username="田中太郎",
            password="password123"
        )
        assert login.username == "田中太郎"


# ============================================
# LoginRequest Tests
# ============================================

class TestLoginRequest:
    """Tests para el modelo LoginRequest (alias de UserLogin)."""

    def test_is_alias_of_user_login(self):
        """Test que es alias de UserLogin."""
        login = LoginRequest(
            username="admin",
            password="password123"
        )
        assert isinstance(login, UserLogin)

    def test_valid_login_request(self):
        """Test request de login valido."""
        login = LoginRequest(
            username="testuser",
            password="securepassword"
        )
        assert login.username == "testuser"


# ============================================
# RefreshRequest Tests
# ============================================

class TestRefreshRequest:
    """Tests para el modelo RefreshRequest."""

    def test_valid_refresh_request(self):
        """Test refresh request valido."""
        request = RefreshRequest(
            refresh_token="eyJhbGciOiJIUzI1NiIs..."
        )
        assert request.refresh_token.startswith("eyJ")

    def test_refresh_token_required(self):
        """Test que refresh_token es requerido."""
        with pytest.raises(ValidationError):
            RefreshRequest()


# ============================================
# RevokeRequest Tests
# ============================================

class TestRevokeRequest:
    """Tests para el modelo RevokeRequest."""

    def test_valid_revoke_request(self):
        """Test revoke request valido."""
        request = RevokeRequest(
            refresh_token="token_to_revoke"
        )
        assert request.refresh_token == "token_to_revoke"


# ============================================
# UserBase Tests
# ============================================

class TestUserBase:
    """Tests para el modelo UserBase."""

    def test_valid_user_base(self):
        """Test base de usuario valida."""
        user = UserBase(
            username="testuser",
            email="test@example.com",
            full_name="Test User"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_username_constraints(self):
        """Test constraints del username."""
        # Muy corto
        with pytest.raises(ValidationError):
            UserBase(
                username="ab",
                email="test@example.com",
                full_name="Test"
            )

        # Muy largo
        with pytest.raises(ValidationError):
            UserBase(
                username="a" * 51,
                email="test@example.com",
                full_name="Test"
            )

    def test_email_validation(self):
        """Test validacion de email."""
        # Email invalido
        with pytest.raises(ValidationError):
            UserBase(
                username="testuser",
                email="invalid-email",
                full_name="Test"
            )

        # Email valido
        user = UserBase(
            username="testuser",
            email="user@example.co.jp",
            full_name="Test"
        )
        assert "@" in user.email

    def test_full_name_constraints(self):
        """Test constraints del nombre completo."""
        # Vacio
        with pytest.raises(ValidationError):
            UserBase(
                username="testuser",
                email="test@example.com",
                full_name=""
            )

        # Muy largo
        with pytest.raises(ValidationError):
            UserBase(
                username="testuser",
                email="test@example.com",
                full_name="a" * 101
            )

    def test_whitespace_stripping(self):
        """Test eliminacion de espacios."""
        user = UserBase(
            username="  testuser  ",
            email="  test@example.com  ",
            full_name="  Test User  "
        )
        assert user.username == "testuser"
        assert user.full_name == "Test User"


# ============================================
# UserCreate Tests
# ============================================

class TestUserCreate:
    """Tests para el modelo UserCreate."""

    def test_valid_user_create(self):
        """Test creacion de usuario valida."""
        user = UserCreate(
            username="newuser",
            email="newuser@example.com",
            full_name="New User",
            password="SecurePass123",
            role=UserRole.USER
        )
        assert user.username == "newuser"
        assert user.role == UserRole.USER

    def test_default_role(self):
        """Test rol por defecto."""
        user = UserCreate(
            username="newuser",
            email="newuser@example.com",
            full_name="New User",
            password="SecurePass123"
        )
        assert user.role == UserRole.USER

    def test_password_validation(self):
        """Test validacion de password."""
        # Muy corta
        with pytest.raises(ValidationError):
            UserCreate(
                username="newuser",
                email="newuser@example.com",
                full_name="New User",
                password="short"
            )

    def test_all_roles_valid(self):
        """Test que todos los roles son validos."""
        for role in UserRole:
            user = UserCreate(
                username="testuser",
                email="test@example.com",
                full_name="Test",
                password="password123",
                role=role
            )
            assert user.role == role

    def test_json_serialization(self):
        """Test serializacion JSON."""
        user = UserCreate(
            username="admin",
            email="admin@example.com",
            full_name="Administrator",
            password="securepass123",
            role=UserRole.ADMIN
        )
        json_str = user.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["username"] == "admin"
        assert parsed["role"] == "admin"


# ============================================
# RegisterRequest Tests
# ============================================

class TestRegisterRequest:
    """Tests para el modelo RegisterRequest."""

    def test_is_alias_of_user_create(self):
        """Test que es alias de UserCreate."""
        request = RegisterRequest(
            username="newuser",
            email="new@example.com",
            full_name="New User",
            password="password123"
        )
        assert isinstance(request, UserCreate)


# ============================================
# UserUpdate Tests
# ============================================

class TestUserUpdate:
    """Tests para el modelo UserUpdate."""

    def test_all_fields_optional(self):
        """Test que todos los campos son opcionales."""
        update = UserUpdate()
        assert update.email is None
        assert update.full_name is None
        assert update.role is None
        assert update.is_active is None

    def test_partial_update(self):
        """Test actualizacion parcial."""
        update = UserUpdate(
            full_name="Updated Name"
        )
        assert update.full_name == "Updated Name"
        assert update.email is None

    def test_email_validation(self):
        """Test validacion de email."""
        with pytest.raises(ValidationError):
            UserUpdate(email="invalid-email")

    def test_update_role(self):
        """Test actualizacion de rol."""
        update = UserUpdate(role=UserRole.MANAGER)
        assert update.role == UserRole.MANAGER

    def test_deactivate_user(self):
        """Test desactivar usuario."""
        update = UserUpdate(is_active=False)
        assert update.is_active is False


# ============================================
# UserResponse Tests
# ============================================

class TestUserResponse:
    """Tests para el modelo UserResponse."""

    def test_valid_response(self):
        """Test respuesta valida."""
        response = UserResponse(
            username="admin",
            email="admin@example.com",
            full_name="Administrator",
            role="admin",
            is_active=True
        )
        assert response.username == "admin"
        assert response.is_active is True

    def test_default_is_active(self):
        """Test is_active por defecto."""
        response = UserResponse(
            username="user",
            email="user@example.com",
            full_name="User",
            role="user"
        )
        assert response.is_active is True

    def test_with_timestamps(self):
        """Test con timestamps."""
        now = datetime.now()
        response = UserResponse(
            username="user",
            email="user@example.com",
            full_name="User",
            role="user",
            created_at=now,
            last_login=now
        )
        assert response.created_at == now
        assert response.last_login == now


# ============================================
# Password Models Tests
# ============================================

class TestChangePasswordRequest:
    """Tests para el modelo ChangePasswordRequest."""

    def test_valid_change_password(self):
        """Test cambio de password valido."""
        request = ChangePasswordRequest(
            current_password="oldpassword123",
            new_password="newSecurePass456"
        )
        assert request.current_password == "oldpassword123"
        assert request.new_password == "newSecurePass456"

    def test_new_password_min_length(self):
        """Test longitud minima de nueva password."""
        with pytest.raises(ValidationError):
            ChangePasswordRequest(
                current_password="oldpassword123",
                new_password="short"
            )

    def test_same_password_invalid(self):
        """Test que password nueva debe ser diferente."""
        with pytest.raises(ValidationError):
            ChangePasswordRequest(
                current_password="samepassword123",
                new_password="samepassword123"
            )


class TestResetPasswordRequest:
    """Tests para el modelo ResetPasswordRequest."""

    def test_valid_reset_request(self):
        """Test reset request valido."""
        request = ResetPasswordRequest(
            email="user@example.com"
        )
        assert request.email == "user@example.com"

    def test_email_required(self):
        """Test que email es requerido."""
        with pytest.raises(ValidationError):
            ResetPasswordRequest()


class TestSetPasswordRequest:
    """Tests para el modelo SetPasswordRequest."""

    def test_valid_set_password(self):
        """Test establecer password valido."""
        request = SetPasswordRequest(
            token="reset_token_12345",
            new_password="newSecurePass123"
        )
        assert request.token == "reset_token_12345"
        assert request.new_password == "newSecurePass123"

    def test_password_min_length(self):
        """Test longitud minima de password."""
        with pytest.raises(ValidationError):
            SetPasswordRequest(
                token="token",
                new_password="short"
            )


# ============================================
# Token Models Tests
# ============================================

class TestTokenResponse:
    """Tests para el modelo TokenResponse."""

    def test_valid_token_response(self):
        """Test respuesta de token valida."""
        response = TokenResponse(
            access_token="eyJhbGciOiJIUzI1NiIs...",
            expires_in=900,
            user={"username": "admin", "role": "admin"}
        )
        assert response.access_token.startswith("eyJ")
        assert response.token_type == "bearer"
        assert response.expires_in == 900

    def test_default_token_type(self):
        """Test tipo de token por defecto."""
        response = TokenResponse(
            access_token="token",
            expires_in=900,
            user={}
        )
        assert response.token_type == "bearer"


class TestTokenPair:
    """Tests para el modelo TokenPair."""

    def test_valid_token_pair(self):
        """Test par de tokens valido."""
        pair = TokenPair(
            access_token="access_token_123",
            refresh_token="refresh_token_456",
            expires_in=900
        )
        assert pair.access_token == "access_token_123"
        assert pair.refresh_token == "refresh_token_456"
        assert pair.token_type == "bearer"


class TestTokenData:
    """Tests para el modelo TokenData."""

    def test_valid_token_data(self):
        """Test datos de token validos."""
        exp = datetime(2025, 1, 17, 12, 0, 0)
        data = TokenData(
            username="admin",
            exp=exp,
            token_type="access"
        )
        assert data.username == "admin"
        assert data.exp == exp
        assert data.token_type == "access"

    def test_default_token_type(self):
        """Test tipo de token por defecto."""
        data = TokenData(
            username="user",
            exp=datetime.now()
        )
        assert data.token_type == "access"


class TestCurrentUser:
    """Tests para el modelo CurrentUser."""

    def test_valid_current_user(self):
        """Test usuario actual valido."""
        user = CurrentUser(
            username="admin",
            role="admin",
            name="Administrator",
            exp=1737120000.0
        )
        assert user.username == "admin"
        assert user.role == "admin"
        assert user.exp == 1737120000.0

    def test_json_serialization(self):
        """Test serializacion JSON."""
        user = CurrentUser(
            username="user",
            role="user",
            name="Normal User",
            exp=1737120000.0
        )
        json_str = user.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["username"] == "user"


# ============================================
# Integration Tests
# ============================================

class TestAuthWorkflow:
    """Tests de flujo de trabajo de autenticacion."""

    def test_login_flow(self):
        """Test flujo de login."""
        # Login request
        login = LoginRequest(
            username="admin",
            password="adminpassword123"
        )

        # Token response
        token = TokenResponse(
            access_token="eyJhbGciOiJIUzI1NiIs...",
            expires_in=900,
            user={
                "username": login.username,
                "role": "admin",
                "name": "Administrator"
            }
        )

        # Current user
        current = CurrentUser(
            username=token.user["username"],
            role=token.user["role"],
            name=token.user["name"],
            exp=1737120000.0
        )

        assert current.username == "admin"
        assert current.role == "admin"

    def test_registration_flow(self):
        """Test flujo de registro."""
        # Register request
        register = RegisterRequest(
            username="newemployee",
            email="employee@company.com",
            full_name="新入社員",
            password="securepassword123",
            role=UserRole.USER
        )

        # User response
        response = UserResponse(
            username=register.username,
            email=register.email,
            full_name=register.full_name,
            role=register.role.value,
            is_active=True,
            created_at=datetime.now()
        )

        assert response.full_name == "新入社員"

    def test_password_change_flow(self):
        """Test flujo de cambio de password."""
        # Change password request
        change = ChangePasswordRequest(
            current_password="oldpassword123",
            new_password="newSecurePass456"
        )

        assert change.current_password != change.new_password

    def test_token_refresh_flow(self):
        """Test flujo de refresh de token."""
        # Initial token pair
        initial = TokenPair(
            access_token="initial_access",
            refresh_token="initial_refresh",
            expires_in=900
        )

        # Refresh request
        refresh = RefreshRequest(
            refresh_token=initial.refresh_token
        )

        # New token pair
        new_pair = TokenPair(
            access_token="new_access",
            refresh_token="new_refresh",
            expires_in=900
        )

        assert new_pair.access_token != initial.access_token

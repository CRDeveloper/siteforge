"""
Tests for authentication handlers (register, login, verify, password reset).
"""
import json
import pytest
import hashlib
import secrets
from datetime import datetime, timedelta, timezone


class TestRegister:
    """Tests for user registration."""

    def test_register_success(self, make_request):
        """Test successful user registration."""
        response = make_request(
            "POST",
            "/auth/register",
            body={
                "email": "newuser@test.local",
                "firstName": "New",
                "lastName": "User",
                "password": "SecurePassword123!",
                "phone": "+1 (555) 111-2222",
            },
        )
        
        assert response["statusCode"] == 201
        body = response["body"]
        assert "message" in body
        assert "created" in body["message"].lower()

    def test_register_missing_email(self, make_request):
        """Test registration with missing email."""
        response = make_request(
            "POST",
            "/auth/register",
            body={
                "firstName": "New",
                "lastName": "User",
                "password": "SecurePassword123!",
            },
        )
        
        assert response["statusCode"] == 400
        body = response["body"]
        assert "error" in body
        assert "invalid email" in body["error"].lower()

    def test_register_invalid_email(self, make_request):
        """Test registration with invalid email format."""
        response = make_request(
            "POST",
            "/auth/register",
            body={
                "email": "not-an-email",
                "firstName": "New",
                "lastName": "User",
                "password": "SecurePassword123!",
            },
        )
        
        assert response["statusCode"] == 400
        body = response["body"]
        assert "error" in body

    def test_register_short_password(self, make_request):
        """Test registration with password too short."""
        response = make_request(
            "POST",
            "/auth/register",
            body={
                "email": "newuser@test.local",
                "firstName": "New",
                "lastName": "User",
                "password": "short",
            },
        )
        
        assert response["statusCode"] == 400
        body = response["body"]
        assert "error" in body
        assert "password" in body["error"].lower()

    def test_register_duplicate_email(self, make_request, seeded_user):
        """Test registration with duplicate email."""
        response = make_request(
            "POST",
            "/auth/register",
            body={
                "email": seeded_user["email"],
                "firstName": "Another",
                "lastName": "User",
                "password": "SecurePassword123!",
            },
        )
        
        assert response["statusCode"] == 409
        body = response["body"]
        assert "error" in body
        assert "already exists" in body["error"].lower()


class TestLogin:
    """Tests for user login."""

    def test_login_success(self, make_request, seeded_user):
        """Test successful login."""
        response = make_request(
            "POST",
            "/auth/login",
            body={
                "email": seeded_user["email"],
                "password": seeded_user["plainPassword"],
            },
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "userId" in body
        assert "firstName" in body
        assert "role" in body
        assert body["role"] == "user"

    def test_login_invalid_email(self, make_request):
        """Test login with non-existent email."""
        response = make_request(
            "POST",
            "/auth/login",
            body={
                "email": "nonexistent@test.local",
                "password": "SomePassword123!",
            },
        )
        
        assert response["statusCode"] == 401
        body = response["body"]
        assert "error" in body

    def test_login_wrong_password(self, make_request, seeded_user):
        """Test login with wrong password."""
        response = make_request(
            "POST",
            "/auth/login",
            body={
                "email": seeded_user["email"],
                "password": "WrongPassword123!",
            },
        )
        
        assert response["statusCode"] == 401
        body = response["body"]
        assert "error" in body

    def test_login_missing_email(self, make_request):
        """Test login with missing email."""
        response = make_request(
            "POST",
            "/auth/login",
            body={
                "password": "SomePassword123!",
            },
        )
        
        assert response["statusCode"] == 400
        body = response["body"]
        assert "error" in body


class TestVerifyEmail:
    """Tests for email verification."""

    def test_verify_email_success(self, make_request, seeded_user):
        """Test successful email verification."""
        # Generate a valid verification token
        verify_token = secrets.token_urlsafe(32)
        verify_token_hash = hashlib.sha256(verify_token.encode()).hexdigest()
        
        # Update the user with the verification token
        from lib.db import update_item
        future_time = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        update_item(
            seeded_user["PK"],
            "PROFILE",
            {
                "verified": False,
                "verifyTokenHash": verify_token_hash,
                "verifyTokenExpiry": future_time,
            },
        )
        
        response = make_request(
            "GET",
            "/auth/verify",
            query={
                "token": verify_token,
                "email": seeded_user["email"],
            },
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "message" in body
        assert "verified" in body["message"].lower()

    def test_verify_email_missing_token(self, make_request):
        """Test verification with missing token."""
        response = make_request(
            "GET",
            "/auth/verify",
            query={
                "email": "test@test.local",
            },
        )
        
        assert response["statusCode"] == 400
        body = response["body"]
        assert "error" in body

    def test_verify_email_invalid_token(self, make_request, seeded_user):
        """Test verification with invalid token."""
        response = make_request(
            "GET",
            "/auth/verify",
            query={
                "token": "invalid-token-that-wont-match",
                "email": seeded_user["email"],
            },
        )
        
        assert response["statusCode"] == 400
        body = response["body"]
        assert "error" in body
        assert "invalid" in body["error"].lower()

    def test_verify_email_expired_token(self, make_request, seeded_user):
        """Test verification with expired token."""
        verify_token = secrets.token_urlsafe(32)
        verify_token_hash = hashlib.sha256(verify_token.encode()).hexdigest()
        
        # Set token expiry to past
        from lib.db import update_item
        past_time = int((datetime.utcnow() - timedelta(hours=1)).timestamp())
        update_item(
            seeded_user["PK"],
            "PROFILE",
            {
                "verified": False,
                "verifyTokenHash": verify_token_hash,
                "verifyTokenExpiry": past_time,
            },
        )
        
        response = make_request(
            "GET",
            "/auth/verify",
            query={
                "token": verify_token,
                "email": seeded_user["email"],
            },
        )
        
        assert response["statusCode"] == 400
        body = response["body"]
        assert "error" in body
        assert "expired" in body["error"].lower()


class TestLogout:
    """Tests for logout."""

    def test_logout_success(self, make_request, test_token):
        """Test successful logout."""
        response = make_request(
            "POST",
            "/auth/logout",
            auth_token=test_token,
        )
        
        assert response["statusCode"] == 200
        body = response["body"]
        assert "message" in body

    def test_logout_without_token(self, make_request):
        """Test logout without authentication."""
        response = make_request(
            "POST",
            "/auth/logout",
        )
        
        # Should succeed even without token (stateless JWT)
        assert response["statusCode"] in [200, 401]


class TestForgotPassword:
    """Tests for forgot password flow."""

    def test_forgot_password_success(self, make_request, seeded_user):
        """Test forgot password request."""
        response = make_request(
            "POST",
            "/auth/forgot-password",
            body={
                "email": seeded_user["email"],
            },
        )
        
        # Should return success even if email doesn't exist (security best practice)
        assert response["statusCode"] == 200
        body = response["body"]
        assert "message" in body

    def test_forgot_password_nonexistent_email(self, make_request):
        """Test forgot password with non-existent email."""
        response = make_request(
            "POST",
            "/auth/forgot-password",
            body={
                "email": "nonexistent@test.local",
            },
        )
        
        # Should return success even if email doesn't exist
        assert response["statusCode"] == 200
        body = response["body"]
        assert "message" in body


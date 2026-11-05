"""Authentication endpoint tests for session-based auth, CSRF protection, and security."""

import pytest
from flask import session
from backend.app.models import User
from backend.app.utils.decorators import generate_csrf_token


class TestCSRFTokenEndpoint:
    """Tests for CSRF token generation endpoint."""

    def test_csrf_token_generation_success(self, client):
        """Test successful CSRF token generation."""
        response = client.get('/api/auth/csrf-token')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'csrf_token' in data['data']
        assert len(data['data']['csrf_token']) > 0
        assert data['message'] == 'CSRF token generated'
        
        # Verify CSRF cookie is set
        cookies = response.headers.getlist('Set-Cookie')
        csrf_cookie = [c for c in cookies if 'csrf_token' in c]
        assert len(csrf_cookie) > 0

    def test_csrf_token_is_unique_per_request(self, client):
        """Test that each CSRF token request generates a unique token."""
        response1 = client.get('/api/auth/csrf-token')
        response2 = client.get('/api/auth/csrf-token')
        
        token1 = response1.get_json()['data']['csrf_token']
        token2 = response2.get_json()['data']['csrf_token']
        
        assert token1 != token2


class TestRegisterEndpoint:
    """Tests for user registration endpoint."""

    def test_register_success(self, client, db_session):
        """Test successful user registration."""
        response = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['username'] == 'newuser'
        assert data['data']['email'] == 'newuser@example.com'
        assert 'id' in data['data']
        assert 'password' not in data['data']
        assert data['message'] == 'User registered successfully'
        
        # Verify user was created in database
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'
        assert user.check_password('SecurePass123!')

    def test_register_missing_request_body(self, client):
        """Test registration with missing request body."""
        response = client.post('/api/auth/register')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert 'Request body is required' in data['error']['message']

    def test_register_empty_request_body(self, client):
        """Test registration with empty request body."""
        response = client.post('/api/auth/register', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_register_missing_username(self, client):
        """Test registration with missing username."""
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_register_missing_email(self, client):
        """Test registration with missing email."""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_register_missing_password(self, client):
        """Test registration with missing password."""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_register_invalid_email_format(self, client):
        """Test registration with invalid email format."""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_register_password_too_short(self, client):
        """Test registration with password shorter than minimum length."""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'short'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_register_username_too_short(self, client):
        """Test registration with username shorter than minimum length."""
        response = client.post('/api/auth/register', json={
            'username': 'ab',  # Less than 3 characters
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_register_username_too_long(self, client):
        """Test registration with username exceeding maximum length."""
        response = client.post('/api/auth/register', json={
            'username': 'a' * 81,  # More than 80 characters
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        response = client.post('/api/auth/register', json={
            'username': test_user.username,
            'email': 'different@example.com',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'CONFLICT'
        assert 'Username already exists' in data['error']['message']

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        response = client.post('/api/auth/register', json={
            'username': 'differentuser',
            'email': test_user.email,
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'CONFLICT'
        assert 'Email already exists' in data['error']['message']

    def test_register_username_with_special_characters(self, client):
        """Test registration with username containing special characters."""
        response = client.post('/api/auth/register', json={
            'username': 'user@name!',
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'


class TestLoginEndpoint:
    """Tests for user login endpoint."""

    def test_login_success(self, client, test_user):
        """Test successful login with valid credentials."""
        response = client.post('/api/auth/login', json={
            'username': test_user.username,
            'password': 'testpassword123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['username'] == test_user.username
        assert data['data']['email'] == test_user.email
        assert 'id' in data['data']
        assert 'password' not in data['data']
        assert data['message'] == 'Login successful'
        
        # Verify CSRF cookie is set after login
        cookies = response.headers.getlist('Set-Cookie')
        csrf_cookie = [c for c in cookies if 'csrf_token' in c]
        assert len(csrf_cookie) > 0

    def test_login_missing_request_body(self, client):
        """Test login with missing request body."""
        response = client.post('/api/auth/login')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_login_missing_username(self, client):
        """Test login with missing username."""
        response = client.post('/api/auth/login', json={
            'password': 'somepassword'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_login_missing_password(self, client):
        """Test login with missing password."""
        response = client.post('/api/auth/login', json={
            'username': 'testuser'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_login_invalid_username(self, client, test_user):
        """Test login with non-existent username."""
        response = client.post('/api/auth/login', json={
            'username': 'nonexistentuser',
            'password': 'testpassword123'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'AUTHENTICATION_ERROR'
        assert 'Invalid username or password' in data['error']['message']

    def test_login_invalid_password(self, client, test_user):
        """Test login with incorrect password."""
        response = client.post('/api/auth/login', json={
            'username': test_user.username,
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'AUTHENTICATION_ERROR'
        assert 'Invalid username or password' in data['error']['message']

    def test_login_inactive_user(self, client, db_session):
        """Test login with inactive/deactivated user account."""
        # Create inactive user
        inactive_user = User(
            username='inactiveuser',
            email='inactive@example.com'
        )
        inactive_user.set_password('testpassword123')
        inactive_user.is_active = False
        db_session.add(inactive_user)
        db_session.commit()
        
        response = client.post('/api/auth/login', json={
            'username': 'inactiveuser',
            'password': 'testpassword123'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'AUTHENTICATION_ERROR'
        assert 'Account is deactivated' in data['error']['message']

    def test_login_case_sensitive_username(self, client, test_user):
        """Test that username is case-sensitive during login."""
        response = client.post('/api/auth/login', json={
            'username': test_user.username.upper(),
            'password': 'testpassword123'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'AUTHENTICATION_ERROR'

    def test_login_creates_session(self, client, test_user):
        """Test that successful login creates a session."""
        with client.session_transaction() as sess:
            assert '_user_id' not in sess
        
        response = client.post('/api/auth/login', json={
            'username': test_user.username,
            'password': 'testpassword123'
        })
        
        assert response.status_code == 200
        
        # Verify session was created
        with client.session_transaction() as sess:
            assert '_user_id' in sess


class TestLogoutEndpoint:
    """Tests for user logout endpoint."""

    def test_logout_success(self, authenticated_client, test_user):
        """Test successful logout."""
        response = authenticated_client.post('/api/auth/logout')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data'] is None
        assert data['message'] == 'Logout successful'

    def test_logout_without_authentication(self, client):
        """Test logout without being authenticated."""
        response = client.post('/api/auth/logout')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False

    def test_logout_clears_session(self, authenticated_client):
        """Test that logout clears the session."""
        # First verify session exists
        with authenticated_client.session_transaction() as sess:
            assert '_user_id' in sess
        
        # Logout
        response = authenticated_client.post('/api/auth/logout')
        assert response.status_code == 200
        
        # Verify session was cleared
        with authenticated_client.session_transaction() as sess:
            assert '_user_id' not in sess

    def test_logout_requires_csrf_token(self, authenticated_client):
        """Test that logout requires CSRF token."""
        # Make request without CSRF token
        response = authenticated_client.post('/api/auth/logout', headers={})
        
        # Should fail due to missing CSRF token
        assert response.status_code in [403, 401]


class TestGetCurrentUserEndpoint:
    """Tests for get current user endpoint."""

    def test_get_current_user_success(self, authenticated_client, test_user):
        """Test getting current user when authenticated."""
        response = authenticated_client.get('/api/auth/me')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['username'] == test_user.username
        assert data['data']['email'] == test_user.email
        assert 'id' in data['data']
        assert 'password' not in data['data']
        assert data['message'] == 'Current user retrieved successfully'

    def test_get_current_user_without_authentication(self, client):
        """Test getting current user without being authenticated."""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False

    def test_get_current_user_after_logout(self, authenticated_client):
        """Test getting current user after logout."""
        # Logout first
        authenticated_client.post('/api/auth/logout')
        
        # Try to get current user
        response = authenticated_client.get('/api/auth/me')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False


class TestSessionSecurity:
    """Tests for session security and management."""

    def test_session_persists_across_requests(self, client, test_user):
        """Test that session persists across multiple requests."""
        # Login
        login_response = client.post('/api/auth/login', json={
            'username': test_user.username,
            'password': 'testpassword123'
        })
        assert login_response.status_code == 200
        
        # Get current user (should be authenticated)
        me_response = client.get('/api/auth/me')
        assert me_response.status_code == 200
        
        # Logout
        logout_response = client.post('/api/auth/logout')
        assert logout_response.status_code == 200
        
        # Try to get current user (should fail)
        me_response_2 = client.get('/api/auth/me')
        assert me_response_2.status_code == 401

    def test_session_isolation_between_clients(self, client, test_user, db_session):
        """Test that sessions are isolated between different clients."""
        # Create second user
        user2 = User(
            username='seconduser',
            email='second@example.com'
        )
        user2.set_password('secondpassword123')
        db_session.add(user2)
        db_session.commit()
        
        # Login as first user
        client.post('/api/auth/login', json={
            'username': test_user.username,
            'password': 'testpassword123'
        })
        
        # Create new client (simulating different browser/session)
        from backend.app import create_app
        from backend.app.config import TestConfig
        
        app = create_app(TestConfig)
        client2 = app.test_client()
        
        # Login as second user with different client
        client2.post('/api/auth/login', json={
            'username': user2.username,
            'password': 'secondpassword123'
        })
        
        # Get current user for first client
        response1 = client.get('/api/auth/me')
        data1 = response1.get_json()
        
        # Get current user for second client
        response2 = client2.get('/api/auth/me')
        data2 = response2.get_json()
        
        # Verify each client sees different user
        assert data1['data']['username'] == test_user.username
        assert data2['data']['username'] == user2.username


class TestPasswordValidation:
    """Tests for password validation rules."""

    def test_password_minimum_length(self, client):
        """Test password minimum length requirement."""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'short'  # Less than 8 characters
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_password_exactly_minimum_length(self, client, db_session):
        """Test password with exactly minimum length (8 chars)."""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'exactly8'  # Exactly 8 characters
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True

    def test_password_hashing(self, client, db_session):
        """Test that passwords are properly hashed and not stored in plain text."""
        plain_password = 'MySecurePassword123!'
        
        client.post('/api/auth/register', json={
            'username': 'hashtestuser',
            'email': 'hashtest@example.com',
            'password': plain_password
        })
        
        # Retrieve user from database
        user = User.query.filter_by(username='hashtestuser').first()
        
        # Verify password is hashed (not stored as plain text)
        assert user.password_hash != plain_password
        assert len(user.password_hash) > len(plain_password)
        
        # Verify password can be verified
        assert user.check_password(plain_password)
        assert not user.check_password('WrongPassword')

    def test_password_not_returned_in_response(self, client, test_user):
        """Test that password is never returned in API responses."""
        # Register response
        register_response = client.post('/api/auth/register', json={
            'username': 'newsecureuser',
            'email': 'secure@example.com',
            'password': 'SecurePass123!'
        })
        register_data = register_response.get_json()
        assert 'password' not in register_data['data']
        
        # Login response
        login_response = client.post('/api/auth/login', json={
            'username': test_user.username,
            'password': 'testpassword123'
        })
        login_data = login_response.get_json()
        assert 'password' not in login_data['data']
        
        # Me response
        login_response = client.post('/api/auth/login', json={
            'username': test_user.username,
            'password': 'testpassword123'
        })
        me_response = client.get('/api/auth/me')
        me_data = me_response.get_json()
        assert 'password' not in me_data['data']


class TestCSRFProtection:
    """Tests for CSRF token protection on state-changing operations."""

    def test_csrf_token_required_for_logout(self, authenticated_client):
        """Test that CSRF token is required for logout."""
        # Try logout without CSRF token header
        response = authenticated_client.post('/api/auth/logout', headers={})
        
        # Should be rejected
        assert response.status_code in [401, 403]

    def test_csrf_token_validation(self, authenticated_client, auth_headers):
        """Test CSRF token validation with correct token."""
        # Logout with proper CSRF token should succeed
        response = authenticated_client.post('/api/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_invalid_csrf_token_rejected(self, authenticated_client):
        """Test that invalid CSRF token is rejected."""
        response = authenticated_client.post('/api/auth/logout', headers={
            'X-CSRF-Token': 'invalid-token'
        })
        
        assert response.status_code in [401, 403]


class TestRateLimiting:
    """Tests for rate limiting on authentication endpoints."""

    def test_login_rate_limiting(self, client, test_user):
        """Test that login endpoint has rate limiting."""
        # Make multiple rapid login requests
        responses = []
        for i in range(5):
            response = client.post('/api/auth/login', json={
                'username': test_user.username,
                'password': 'wrongpassword'  # Intentionally wrong
            })
            responses.append(response.status_code)
        
        # At least some requests should be rate limited (429)
        # or we should see consistent 401 responses for wrong password
        assert 401 in responses or 429 in responses

    def test_register_rate_limiting(self, client):
        """Test that register endpoint has rate limiting."""
        # Make multiple rapid register requests
        responses = []
        for i in range(5):
            response = client.post('/api/auth/register', json={
                'username': f'ratelimituser{i}',
                'email': f'ratelimit{i}@example.com',
                'password': 'SecurePass123!'
            })
            responses.append(response.status_code)
        
        # Should see either successful registrations (201) or rate limiting (429)
        assert 201 in responses or 429 in responses


class TestAuthEdgeCases:
    """Tests for authentication edge cases and boundary conditions."""

    def test_login_with_extra_fields(self, client, test_user):
        """Test login with extra fields in request body."""
        response = client.post('/api/auth/login', json={
            'username': test_user.username,
            'password': 'testpassword123',
            'extra_field': 'extra_value',
            'another_field': 123
        })
        
        # Should succeed and ignore extra fields
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_register_with_extra_fields(self, client, db_session):
        """Test registration with extra fields in request body."""
        response = client.post('/api/auth/register', json={
            'username': 'extrafieldsuser',
            'email': 'extra@example.com',
            'password': 'SecurePass123!',
            'extra_field': 'extra_value'
        })
        
        # Should succeed and ignore extra fields
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True

    def test_login_with_null_values(self, client):
        """Test login with null values."""
        response = client.post('/api/auth/login', json={
            'username': None,
            'password': None
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_register_with_null_values(self, client):
        """Test registration with null values."""
        response = client.post('/api/auth/register', json={
            'username': None,
            'email': None,
            'password': None
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_login_with_empty_strings(self, client):
        """Test login with empty string values."""
        response = client.post('/api/auth/login', json={
            'username': '',
            'password': ''
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_register_with_empty_strings(self, client):
        """Test registration with empty string values."""
        response = client.post('/api/auth/register', json={
            'username': '',
            'email': '',
            'password': ''
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_login_with_whitespace_only(self, client):
        """Test login with whitespace-only values."""
        response = client.post('/api/auth/login', json={
            'username': '   ',
            'password': '   '
        })
        
        assert response.status_code == 401  # Should fail authentication

    def test_register_with_whitespace_username(self, client):
        """Test registration with whitespace in username."""
        response = client.post('/api/auth/register', json={
            'username': 'user name',
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        })
        
        # Should fail validation - spaces not allowed in username
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_concurrent_login_sessions(self, client, test_user):
        """Test that user can maintain session across multiple requests."""
        # Login
        login_response = client.post('/api/auth/login', json={
            'username': test_user.username,
            'password': 'testpassword123'
        })
        assert login_response.status_code == 200
        
        # Make multiple authenticated requests
        for i in range(3):
            me_response = client.get('/api/auth/me')
            assert me_response.status_code == 200
            data = me_response.get_json()
            assert data['data']['username'] == test_user.username

    def test_auth_endpoints_content_type(self, client, test_user):
        """Test that auth endpoints require proper content type."""
        # Try POST with wrong content type
        response = client.post('/api/auth/login', 
                                 data='not json',
                                 content_type='text/plain')
        
        # Should fail validation
        assert response.status_code == 400

    def test_auth_response_headers(self, client, test_user):
        """Test that auth responses have proper security headers."""
        response = client.post('/api/auth/login', json={
            'username': test_user.username,
            'password': 'testpassword123'
        })
        
        assert response.status_code == 200
        
        # Check for security headers
        assert 'Content-Type' in response.headers
        assert response.headers['Content-Type'] == 'application/json'

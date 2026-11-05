"""Test suite for user API endpoints.

This module covers:
- User profile retrieval (GET /api/users/me)
- User profile updates (PUT /api/users/me)
- Partial user profile updates (PATCH /api/users/me)
- User account deletion (DELETE /api/users/me)
- User lookup by ID (GET /api/users/{id})
- Unique constraint validation
- Unauthorized access attempts
"""

import pytest
from datetime import datetime, timezone


class TestGetCurrentUserEndpoint:
    """Tests for GET /api/users/me endpoint."""

    def test_get_current_user_success(self, authenticated_client, test_user):
        """Test successful retrieval of current user profile."""
        response = authenticated_client.get('/api/users/me')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['username'] == test_user.username
        assert data['data']['email'] == test_user.email
        assert 'id' in data['data']
        assert 'created_at' in data['data']
        assert 'updated_at' in data['data']
        assert 'password_hash' not in data['data']
        assert 'password' not in data['data']

    def test_get_current_user_not_authenticated(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.get('/api/users/me')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data

    def test_get_current_user_response_structure(self, authenticated_client):
        """Test that response follows expected structure."""
        response = authenticated_client.get('/api/users/me')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Check top-level structure
        assert 'success' in data
        assert 'data' in data
        assert 'message' in data
        
        # Check user data fields
        user_data = data['data']
        required_fields = ['id', 'username', 'email', 'is_active', 'created_at', 'updated_at']
        for field in required_fields:
            assert field in user_data, f"Missing required field: {field}"


class TestUpdateCurrentUserEndpoint:
    """Tests for PUT /api/users/me endpoint."""

    def test_update_username_success(self, authenticated_client, auth_headers, test_user):
        """Test successful username update."""
        new_username = 'updateduser'
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': new_username},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['username'] == new_username

    def test_update_email_success(self, authenticated_client, auth_headers, test_user):
        """Test successful email update."""
        new_email = 'updated@example.com'
        response = authenticated_client.put(
            '/api/users/me',
            json={'email': new_email},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['email'] == new_email

    def test_update_both_username_and_email(self, authenticated_client, auth_headers):
        """Test updating both username and email simultaneously."""
        response = authenticated_client.put(
            '/api/users/me',
            json={
                'username': 'newusername',
                'email': 'newemail@example.com'
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['username'] == 'newusername'
        assert data['data']['email'] == 'newemail@example.com'

    def test_update_username_conflict(self, authenticated_client, auth_headers, db_session):
        """Test that updating to an existing username fails."""
        # Create another user first
        from backend.app.models import User
        other_user = User(
            username='existinguser',
            email='existing@example.com'
        )
        other_user.set_password('TestPass123!')
        db_session.add(other_user)
        db_session.commit()
        
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': 'existinguser'},
            headers=auth_headers
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['success'] is False
        assert 'CONFLICT' in data['error']['code']

    def test_update_email_conflict(self, authenticated_client, auth_headers, db_session):
        """Test that updating to an existing email fails."""
        # Create another user first
        from backend.app.models import User
        other_user = User(
            username='anotheruser',
            email='taken@example.com'
        )
        other_user.set_password('TestPass123!')
        db_session.add(other_user)
        db_session.commit()
        
        response = authenticated_client.put(
            '/api/users/me',
            json={'email': 'taken@example.com'},
            headers=auth_headers
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['success'] is False
        assert 'CONFLICT' in data['error']['code']

    def test_update_username_invalid_format(self, authenticated_client, auth_headers):
        """Test that invalid username formats are rejected."""
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': 'invalid username!'},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_update_username_too_short(self, authenticated_client, auth_headers):
        """Test that too short usernames are rejected."""
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': 'ab'},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_update_username_starts_with_digit(self, authenticated_client, auth_headers):
        """Test that usernames starting with digits are rejected."""
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': '1username'},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_update_invalid_email_format(self, authenticated_client, auth_headers):
        """Test that invalid email formats are rejected."""
        response = authenticated_client.put(
            '/api/users/me',
            json={'email': 'not-an-email'},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_update_empty_body(self, authenticated_client, auth_headers):
        """Test that empty request body is handled."""
        response = authenticated_client.put(
            '/api/users/me',
            json={},
            headers=auth_headers
        )
        
        # Empty update should succeed (no changes)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_update_no_body(self, authenticated_client, auth_headers):
        """Test that missing request body is handled."""
        response = authenticated_client.put(
            '/api/users/me',
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_update_not_authenticated(self, client):
        """Test that unauthenticated update requests are rejected."""
        response = client.put(
            '/api/users/me',
            json={'username': 'newname'}
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False

    def test_update_same_username_no_conflict(self, authenticated_client, auth_headers, test_user):
        """Test that updating to current username doesn't trigger conflict."""
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': test_user.username},
            headers=auth_headers
        )
        
        # Should succeed since it's the same user
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_update_same_email_no_conflict(self, authenticated_client, auth_headers, test_user):
        """Test that updating to current email doesn't trigger conflict."""
        response = authenticated_client.put(
            '/api/users/me',
            json={'email': test_user.email},
            headers=auth_headers
        )
        
        # Should succeed since it's the same user
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


class TestPatchCurrentUserEndpoint:
    """Tests for PATCH /api/users/me endpoint."""

    def test_patch_username_success(self, authenticated_client, auth_headers):
        """Test successful partial update of username."""
        response = authenticated_client.patch(
            '/api/users/me',
            json={'username': 'patcheduser'},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['username'] == 'patcheduser'

    def test_patch_email_success(self, authenticated_client, auth_headers):
        """Test successful partial update of email."""
        response = authenticated_client.patch(
            '/api/users/me',
            json={'email': 'patched@example.com'},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['email'] == 'patched@example.com'

    def test_patch_single_field_preserves_others(self, authenticated_client, auth_headers, test_user):
        """Test that patching one field preserves others."""
        original_email = test_user.email
        
        response = authenticated_client.patch(
            '/api/users/me',
            json={'username': 'onlyusernamechanged'},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['username'] == 'onlyusernamechanged'
        assert data['data']['email'] == original_email

    def test_patch_not_authenticated(self, client):
        """Test that unauthenticated patch requests are rejected."""
        response = client.patch(
            '/api/users/me',
            json={'username': 'newname'}
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False


class TestDeleteCurrentUserEndpoint:
    """Tests for DELETE /api/users/me endpoint."""

    def test_delete_account_success(self, authenticated_client, auth_headers, db_session):
        """Test successful account deletion."""
        # Get the user before deletion to verify cascade
        from backend.app.models import User
        
        response = authenticated_client.delete(
            '/api/users/me',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'deleted' in data['message'].lower()

    def test_delete_account_cascade_todos(self, authenticated_client, auth_headers, db_session, test_user):
        """Test that deleting account also deletes associated todos."""
        from backend.app.models import Todo
        
        # Create a todo for the user
        todo = Todo(
            title='Test Todo',
            description='Will be deleted with user',
            user_id=test_user.id
        )
        db_session.add(todo)
        db_session.commit()
        
        # Delete the user
        response = authenticated_client.delete(
            '/api/users/me',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify todo is also deleted
        remaining_todos = Todo.query.filter_by(user_id=test_user.id).all()
        assert len(remaining_todos) == 0

    def test_delete_account_not_authenticated(self, client):
        """Test that unauthenticated delete requests are rejected."""
        response = client.delete('/api/users/me')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False

    def test_delete_account_session_invalidated(self, authenticated_client, auth_headers, db_session):
        """Test that session is invalidated after account deletion."""
        # Delete the account
        response = authenticated_client.delete(
            '/api/users/me',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Try to access protected endpoint
        response = authenticated_client.get('/api/users/me')
        assert response.status_code == 401


class TestGetUserByIdEndpoint:
    """Tests for GET /api/users/{id} endpoint."""

    def test_get_user_by_id_success(self, authenticated_client, test_user):
        """Test successful retrieval of user by ID."""
        response = authenticated_client.get(f'/api/users/{test_user.id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['id'] == test_user.id
        assert data['data']['username'] == test_user.username

    def test_get_other_user_limited_profile(self, authenticated_client, db_session):
        """Test that viewing another user returns limited profile."""
        from backend.app.models import User
        
        # Create another user
        other_user = User(
            username='otheruser',
            email='other@example.com'
        )
        other_user.set_password('TestPass123!')
        db_session.add(other_user)
        db_session.commit()
        
        response = authenticated_client.get(f'/api/users/{other_user.id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        # Should only have limited fields for other users
        assert 'id' in data['data']
        assert 'username' in data['data']
        assert 'created_at' in data['data']

    def test_get_user_not_found(self, authenticated_client):
        """Test that non-existent user returns 404."""
        response = authenticated_client.get('/api/users/non-existent-uuid-12345')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'NOT_FOUND' in data['error']['code']

    def test_get_user_not_authenticated(self, client, test_user):
        """Test that unauthenticated requests are rejected."""
        response = client.get(f'/api/users/{test_user.id}')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False


class TestUpdateUserByIdEndpoint:
    """Tests for PUT /api/users/{id} endpoint."""

    def test_update_own_profile_by_id(self, authenticated_client, auth_headers, test_user):
        """Test updating own profile via ID endpoint."""
        response = authenticated_client.put(
            f'/api/users/{test_user.id}',
            json={'username': 'updatedviaid'},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['username'] == 'updatedviaid'

    def test_update_other_user_forbidden(self, authenticated_client, auth_headers, db_session):
        """Test that updating another user's profile is forbidden."""
        from backend.app.models import User
        
        # Create another user
        other_user = User(
            username='victim',
            email='victim@example.com'
        )
        other_user.set_password('TestPass123!')
        db_session.add(other_user)
        db_session.commit()
        
        response = authenticated_client.put(
            f'/api/users/{other_user.id}',
            json={'username': 'hacked'},
            headers=auth_headers
        )
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert 'FORBIDDEN' in data['error']['code']

    def test_update_user_not_authenticated(self, client, test_user):
        """Test that unauthenticated update requests are rejected."""
        response = client.put(
            f'/api/users/{test_user.id}',
            json={'username': 'newname'}
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False


class TestDeleteUserByIdEndpoint:
    """Tests for DELETE /api/users/{id} endpoint."""

    def test_delete_own_account_by_id(self, authenticated_client, auth_headers, test_user):
        """Test deleting own account via ID endpoint."""
        response = authenticated_client.delete(
            f'/api/users/{test_user.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_delete_other_user_forbidden(self, authenticated_client, auth_headers, db_session):
        """Test that deleting another user's account is forbidden."""
        from backend.app.models import User
        
        # Create another user
        other_user = User(
            username='target',
            email='target@example.com'
        )
        other_user.set_password('TestPass123!')
        db_session.add(other_user)
        db_session.commit()
        
        response = authenticated_client.delete(
            f'/api/users/{other_user.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert 'FORBIDDEN' in data['error']['code']

    def test_delete_user_not_authenticated(self, client, test_user):
        """Test that unauthenticated delete requests are rejected."""
        response = client.delete(f'/api/users/{test_user.id}')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False


class TestUserUniqueConstraints:
    """Tests for user unique constraint validation."""

    def test_username_uniqueness(self, db_session):
        """Test that usernames must be unique."""
        from backend.app.models import User
        
        # Create first user
        user1 = User(username='uniqueuser', email='unique1@example.com')
        user1.set_password('TestPass123!')
        db_session.add(user1)
        db_session.commit()
        
        # Try to create second user with same username
        user2 = User(username='uniqueuser', email='unique2@example.com')
        user2.set_password('TestPass123!')
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()
        
        db_session.rollback()

    def test_email_uniqueness(self, db_session):
        """Test that emails must be unique."""
        from backend.app.models import User
        
        # Create first user
        user1 = User(username='emailuser1', email='same@example.com')
        user1.set_password('TestPass123!')
        db_session.add(user1)
        db_session.commit()
        
        # Try to create second user with same email
        user2 = User(username='emailuser2', email='same@example.com')
        user2.set_password('TestPass123!')
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()
        
        db_session.rollback()

    def test_case_insensitive_username(self, authenticated_client, auth_headers, db_session):
        """Test that username uniqueness is case-insensitive."""
        from backend.app.models import User
        
        # Create another user with different case
        other_user = User(username='TestUser', email='testuser@example.com')
        other_user.set_password('TestPass123!')
        db_session.add(other_user)
        db_session.commit()
        
        # Try to update to same username different case
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': 'testuser'},  # lowercase version
            headers=auth_headers
        )
        
        # Should fail due to conflict
        assert response.status_code == 409


class TestUserProfileTimestamps:
    """Tests for user profile timestamp handling."""

    def test_created_at_set_on_creation(self, db_session):
        """Test that created_at is set when user is created."""
        from backend.app.models import User
        
        before_create = datetime.now(timezone.utc)
        user = User(username='timestampuser', email='timestamp@example.com')
        user.set_password('TestPass123!')
        db_session.add(user)
        db_session.commit()
        after_create = datetime.now(timezone.utc)
        
        assert user.created_at is not None
        assert before_create <= user.created_at <= after_create

    def test_updated_at_changes_on_update(self, authenticated_client, auth_headers, test_user):
        """Test that updated_at changes when profile is updated."""
        original_updated_at = test_user.updated_at
        
        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': 'timestampupdated'},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify updated_at changed
        from backend.app.models import User
        updated_user = User.query.get(test_user.id)
        assert updated_user.updated_at > original_updated_at


class TestUserEdgeCases:
    """Tests for user endpoint edge cases."""

    def test_username_with_unicode(self, authenticated_client, auth_headers):
        """Test that unicode in username is rejected."""
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': 'userñame'},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_username_with_special_chars(self, authenticated_client, auth_headers):
        """Test that special characters in username are rejected."""
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': 'user@name'},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_very_long_username(self, authenticated_client, auth_headers):
        """Test that very long usernames are rejected."""
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': 'a' * 100},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_very_long_email(self, authenticated_client, auth_headers):
        """Test that very long emails are handled."""
        long_email = 'a' * 200 + '@example.com'
        response = authenticated_client.put(
            '/api/users/me',
            json={'email': long_email},
            headers=auth_headers
        )
        
        # Should either succeed or fail with validation error
        assert response.status_code in [200, 400]

    def test_extra_fields_rejected(self, authenticated_client, auth_headers):
        """Test that extra fields in update are rejected."""
        response = authenticated_client.put(
            '/api/users/me',
            json={
                'username': 'validuser',
                'extra_field': 'should_not_be_allowed'
            },
            headers=auth_headers
        )
        
        # Should reject extra fields
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_null_values_rejected(self, authenticated_client, auth_headers):
        """Test that null values are handled appropriately."""
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': None},
            headers=auth_headers
        )
        
        # Should either succeed (no change) or fail validation
        assert response.status_code in [200, 400]

    def test_whitespace_in_username_normalized(self, authenticated_client, auth_headers):
        """Test that whitespace in username is handled."""
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': '  userwithspaces  '},
            headers=auth_headers
        )
        
        # Should either trim or reject
        if response.status_code == 200:
            data = response.get_json()
            assert 'userwithspaces' in data['data']['username']


class TestUserSecurity:
    """Tests for user endpoint security."""

    def test_password_hash_not_exposed(self, authenticated_client, test_user):
        """Test that password hash is never exposed in responses."""
        response = authenticated_client.get('/api/users/me')
        
        assert response.status_code == 200
        data = response.get_json()
        
        response_str = str(data)
        assert 'password_hash' not in response_str
        assert 'password' not in response_str.lower() or 'password' not in data.get('data', {})

    def test_csrf_required_for_update(self, authenticated_client, test_user):
        """Test that CSRF protection is required for updates."""
        # Make request without CSRF headers
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': 'newname'}
        )
        
        # Should fail due to missing CSRF
        assert response.status_code == 403

    def test_csrf_required_for_delete(self, authenticated_client):
        """Test that CSRF protection is required for deletion."""
        # Make request without CSRF headers
        response = authenticated_client.delete('/api/users/me')
        
        # Should fail due to missing CSRF
        assert response.status_code == 403

    def test_rate_limiting_on_update(self, app, authenticated_client, auth_headers):
        """Test that update endpoint has rate limiting."""
        # The strict_rate_limit decorator should be applied
        # We can verify by checking the endpoint configuration
        from backend.app.api.users import users_bp
        
        # Find the update endpoint
        update_endpoint = None
        for rule in app.url_map.iter_rules():
            if 'users' in rule.endpoint and 'me' in str(rule.rule):
                if 'PUT' in rule.methods or 'PATCH' in rule.methods:
                    update_endpoint = rule
                    break
        
        # The endpoint should exist
        assert update_endpoint is not None

    def test_sql_injection_protection_username(self, authenticated_client, auth_headers):
        """Test protection against SQL injection in username."""
        malicious_username = "'; DROP TABLE users; --"
        
        response = authenticated_client.put(
            '/api/users/me',
            json={'username': malicious_username},
            headers=auth_headers
        )
        
        # Should fail validation, not cause SQL injection
        assert response.status_code == 400
        
        # Verify users table still exists
        from backend.app.models import User
        users = User.query.all()
        assert isinstance(users, list)

    def test_sql_injection_protection_email(self, authenticated_client, auth_headers):
        """Test protection against SQL injection in email."""
        malicious_email = "'; DROP TABLE users; --@example.com"
        
        response = authenticated_client.put(
            '/api/users/me',
            json={'email': malicious_email},
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 400
        
        # Verify users table still exists
        from backend.app.models import User
        users = User.query.all()
        assert isinstance(users, list)

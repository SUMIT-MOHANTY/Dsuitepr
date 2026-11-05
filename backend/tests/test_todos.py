"""Comprehensive tests for Todo API endpoints.

This module covers all 11 todo endpoints:
- GET /api/todos (list with filtering, pagination)
- POST /api/todos (create)
- GET /api/todos/{id} (get single)
- PUT /api/todos/{id} (full update)
- PATCH /api/todos/{id} (partial update)
- DELETE /api/todos/{id} (delete)
- PATCH /api/todos/{id}/complete (mark complete)
- PATCH /api/todos/{id}/incomplete (mark incomplete)
- GET /api/todos/stats (statistics)
- POST /api/todos/bulk (bulk update)
- DELETE /api/todos/completed (clear completed)
- POST /api/todos/bulk-delete (bulk delete)
"""

import pytest
from datetime import datetime, timezone, timedelta
from flask import session

from backend.app.models import Todo, User
from backend.app.models.todo import PriorityLevel


class TestGetTodos:
    """Tests for GET /api/todos endpoint."""

    def test_get_todos_success(self, authenticated_client, test_user, db_session):
        """Test successful retrieval of todos list."""
        # Create test todos
        todo1 = Todo(
            user_id=test_user.id,
            title="Test Todo 1",
            description="Description 1",
            priority=PriorityLevel.MEDIUM.value,
            is_completed=False
        )
        todo2 = Todo(
            user_id=test_user.id,
            title="Test Todo 2",
            priority=PriorityLevel.HIGH.value,
            is_completed=True
        )
        db_session.add_all([todo1, todo2])
        db_session.commit()

        response = authenticated_client.get('/api/todos')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'items' in data['data']
        assert len(data['data']['items']) == 2
        assert data['data']['total'] == 2

    def test_get_todos_empty_list(self, authenticated_client):
        """Test retrieval when user has no todos."""
        response = authenticated_client.get('/api/todos')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['items'] == []
        assert data['data']['total'] == 0

    def test_get_todos_unauthorized(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.get('/api/todos')
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data

    def test_get_todos_filter_by_status_active(self, authenticated_client, test_user, db_session):
        """Test filtering todos by active status."""
        todo1 = Todo(
            user_id=test_user.id,
            title="Active Todo",
            is_completed=False
        )
        todo2 = Todo(
            user_id=test_user.id,
            title="Completed Todo",
            is_completed=True
        )
        db_session.add_all([todo1, todo2])
        db_session.commit()

        response = authenticated_client.get('/api/todos?status=active')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['items']) == 1
        assert data['data']['items'][0]['title'] == "Active Todo"

    def test_get_todos_filter_by_status_completed(self, authenticated_client, test_user, db_session):
        """Test filtering todos by completed status."""
        todo1 = Todo(
            user_id=test_user.id,
            title="Active Todo",
            is_completed=False
        )
        todo2 = Todo(
            user_id=test_user.id,
            title="Completed Todo",
            is_completed=True
        )
        db_session.add_all([todo1, todo2])
        db_session.commit()

        response = authenticated_client.get('/api/todos?status=completed')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['items']) == 1
        assert data['data']['items'][0]['title'] == "Completed Todo"

    def test_get_todos_filter_by_priority(self, authenticated_client, test_user, db_session):
        """Test filtering todos by priority."""
        todo1 = Todo(
            user_id=test_user.id,
            title="High Priority",
            priority=PriorityLevel.HIGH.value,
            is_completed=False
        )
        todo2 = Todo(
            user_id=test_user.id,
            title="Low Priority",
            priority=PriorityLevel.LOW.value,
            is_completed=False
        )
        db_session.add_all([todo1, todo2])
        db_session.commit()

        response = authenticated_client.get('/api/todos?priority=high')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['items']) == 1
        assert data['data']['items'][0]['priority'] == 'high'

    def test_get_todos_search(self, authenticated_client, test_user, db_session):
        """Test searching todos by title/description."""
        todo1 = Todo(
            user_id=test_user.id,
            title="Shopping List",
            description="Buy groceries",
            is_completed=False
        )
        todo2 = Todo(
            user_id=test_user.id,
            title="Work Task",
            description="Complete project",
            is_completed=False
        )
        db_session.add_all([todo1, todo2])
        db_session.commit()

        response = authenticated_client.get('/api/todos?search=shopping')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['items']) == 1
        assert 'Shopping' in data['data']['items'][0]['title']

    def test_get_todos_pagination(self, authenticated_client, test_user, db_session):
        """Test pagination of todos."""
        # Create 15 todos
        todos = []
        for i in range(15):
            todo = Todo(
                user_id=test_user.id,
                title=f"Todo {i}",
                is_completed=False
            )
            todos.append(todo)
        db_session.add_all(todos)
        db_session.commit()

        response = authenticated_client.get('/api/todos?page=1&per_page=10')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['items']) == 10
        assert data['data']['total'] == 15
        assert data['data']['pages'] == 2

    def test_get_todos_sorting(self, authenticated_client, test_user, db_session):
        """Test sorting of todos."""
        todo1 = Todo(
            user_id=test_user.id,
            title="Alpha",
            is_completed=False
        )
        todo2 = Todo(
            user_id=test_user.id,
            title="Beta",
            is_completed=False
        )
        db_session.add_all([todo1, todo2])
        db_session.commit()

        response = authenticated_client.get('/api/todos?sort_by=title&sort_order=asc')
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['items'][0]['title'] == "Alpha"
        assert data['data']['items'][1]['title'] == "Beta"

    def test_get_todos_isolation_between_users(self, authenticated_client, test_user, test_user_2, db_session):
        """Test that users can only see their own todos."""
        todo1 = Todo(
            user_id=test_user.id,
            title="User 1 Todo",
            is_completed=False
        )
        todo2 = Todo(
            user_id=test_user_2.id,
            title="User 2 Todo",
            is_completed=False
        )
        db_session.add_all([todo1, todo2])
        db_session.commit()

        response = authenticated_client.get('/api/todos')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['items']) == 1
        assert data['data']['items'][0]['title'] == "User 1 Todo"


class TestCreateTodo:
    """Tests for POST /api/todos endpoint."""

    def test_create_todo_success(self, authenticated_client, auth_headers):
        """Test successful todo creation."""
        payload = {
            'title': 'New Todo',
            'description': 'A test todo',
            'priority': 'medium'
        }
        response = authenticated_client.post(
            '/api/todos',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == 'New Todo'
        assert data['data']['description'] == 'A test todo'
        assert data['data']['priority'] == 'medium'
        assert data['data']['is_completed'] is False

    def test_create_todo_minimal(self, authenticated_client, auth_headers):
        """Test creating todo with only required fields."""
        payload = {
            'title': 'Minimal Todo'
        }
        response = authenticated_client.post(
            '/api/todos',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == 'Minimal Todo'
        assert data['data']['priority'] == 'medium'  # default

    def test_create_todo_missing_title(self, authenticated_client, auth_headers):
        """Test that missing title returns validation error."""
        payload = {
            'description': 'No title provided'
        }
        response = authenticated_client.post(
            '/api/todos',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data

    def test_create_todo_empty_title(self, authenticated_client, auth_headers):
        """Test that empty title returns validation error."""
        payload = {
            'title': ''
        }
        response = authenticated_client.post(
            '/api/todos',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_create_todo_title_too_long(self, authenticated_client, auth_headers):
        """Test that overly long title returns validation error."""
        payload = {
            'title': 'x' * 201  # Assuming max is 200
        }
        response = authenticated_client.post(
            '/api/todos',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_create_todo_with_due_date(self, authenticated_client, auth_headers):
        """Test creating todo with due date."""
        due_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        payload = {
            'title': 'Scheduled Todo',
            'due_date': due_date
        }
        response = authenticated_client.post(
            '/api/todos',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['due_date'] is not None

    def test_create_todo_unauthorized(self, client):
        """Test that unauthenticated requests are rejected."""
        payload = {'title': 'Unauthorized Todo'}
        response = client.post('/api/todos', json=payload)
        assert response.status_code == 401

    def test_create_todo_missing_csrf_token(self, authenticated_client):
        """Test that missing CSRF token is rejected."""
        payload = {'title': 'No CSRF Todo'}
        response = authenticated_client.post('/api/todos', json=payload)
        assert response.status_code == 403


class TestGetTodo:
    """Tests for GET /api/todos/{id} endpoint."""

    def test_get_todo_success(self, authenticated_client, test_user, db_session):
        """Test successful retrieval of single todo."""
        todo = Todo(
            user_id=test_user.id,
            title="Single Todo",
            description="Test description",
            priority=PriorityLevel.HIGH.value,
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        response = authenticated_client.get(f'/api/todos/{todo.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == "Single Todo"
        assert data['data']['description'] == "Test description"

    def test_get_todo_not_found(self, authenticated_client):
        """Test 404 for non-existent todo."""
        response = authenticated_client.get('/api/todos/non-existent-id')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'NOT_FOUND'

    def test_get_todo_other_users_todo(self, authenticated_client, test_user_2, db_session):
        """Test that users cannot access other users' todos."""
        todo = Todo(
            user_id=test_user_2.id,
            title="Other User's Todo",
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        response = authenticated_client.get(f'/api/todos/{todo.id}')
        assert response.status_code == 404

    def test_get_todo_unauthorized(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.get('/api/todos/some-id')
        assert response.status_code == 401


class TestUpdateTodo:
    """Tests for PUT /api/todos/{id} endpoint."""

    def test_update_todo_success(self, authenticated_client, test_user, db_session, auth_headers):
        """Test successful full update of todo."""
        todo = Todo(
            user_id=test_user.id,
            title="Original Title",
            description="Original description",
            priority=PriorityLevel.LOW.value,
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        payload = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'priority': 'high',
            'is_completed': True
        }
        response = authenticated_client.put(
            f'/api/todos/{todo.id}',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == 'Updated Title'
        assert data['data']['priority'] == 'high'
        assert data['data']['is_completed'] is True

    def test_update_todo_not_found(self, authenticated_client, auth_headers):
        """Test 404 when updating non-existent todo."""
        payload = {
            'title': 'Updated Title',
            'priority': 'medium',
            'is_completed': False
        }
        response = authenticated_client.put(
            '/api/todos/non-existent-id',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_todo_other_users_todo(self, authenticated_client, test_user_2, db_session, auth_headers):
        """Test that users cannot update other users' todos."""
        todo = Todo(
            user_id=test_user_2.id,
            title="Other User's Todo",
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        payload = {'title': 'Hacked Title', 'priority': 'medium', 'is_completed': False}
        response = authenticated_client.put(
            f'/api/todos/{todo.id}',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_todo_missing_body(self, authenticated_client, test_user, db_session, auth_headers):
        """Test that missing request body returns error."""
        todo = Todo(
            user_id=test_user.id,
            title="Todo",
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        response = authenticated_client.put(
            f'/api/todos/{todo.id}',
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_update_todo_unauthorized(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.put('/api/todos/some-id', json={'title': 'Test'})
        assert response.status_code == 401


class TestPatchTodo:
    """Tests for PATCH /api/todos/{id} endpoint."""

    def test_patch_todo_partial_update(self, authenticated_client, test_user, db_session, auth_headers):
        """Test successful partial update of todo."""
        todo = Todo(
            user_id=test_user.id,
            title="Original Title",
            description="Original description",
            priority=PriorityLevel.MEDIUM.value,
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        payload = {'title': 'Patched Title'}
        response = authenticated_client.patch(
            f'/api/todos/{todo.id}',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == 'Patched Title'
        # Other fields should remain unchanged
        assert data['data']['description'] == "Original description"

    def test_patch_todo_priority_only(self, authenticated_client, test_user, db_session, auth_headers):
        """Test patching only priority field."""
        todo = Todo(
            user_id=test_user.id,
            title="Todo",
            priority=PriorityLevel.LOW.value,
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        payload = {'priority': 'high'}
        response = authenticated_client.patch(
            f'/api/todos/{todo.id}',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['priority'] == 'high'


class TestDeleteTodo:
    """Tests for DELETE /api/todos/{id} endpoint."""

    def test_delete_todo_success(self, authenticated_client, test_user, db_session, auth_headers):
        """Test successful deletion of todo."""
        todo = Todo(
            user_id=test_user.id,
            title="Todo to Delete",
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()
        todo_id = todo.id

        response = authenticated_client.delete(
            f'/api/todos/{todo_id}',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'message' in data

        # Verify deletion
        deleted_todo = db_session.get(Todo, todo_id)
        assert deleted_todo is None

    def test_delete_todo_not_found(self, authenticated_client, auth_headers):
        """Test 404 when deleting non-existent todo."""
        response = authenticated_client.delete(
            '/api/todos/non-existent-id',
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_delete_todo_other_users_todo(self, authenticated_client, test_user_2, db_session, auth_headers):
        """Test that users cannot delete other users' todos."""
        todo = Todo(
            user_id=test_user_2.id,
            title="Other User's Todo",
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        response = authenticated_client.delete(
            f'/api/todos/{todo.id}',
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_delete_todo_unauthorized(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.delete('/api/todos/some-id')
        assert response.status_code == 401


class TestMarkComplete:
    """Tests for PATCH /api/todos/{id}/complete endpoint."""

    def test_mark_complete_success(self, authenticated_client, test_user, db_session, auth_headers):
        """Test successfully marking todo as complete."""
        todo = Todo(
            user_id=test_user.id,
            title="Incomplete Todo",
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        response = authenticated_client.patch(
            f'/api/todos/{todo.id}/complete',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_completed'] is True
        assert data['data']['completed_at'] is not None

    def test_mark_complete_already_complete(self, authenticated_client, test_user, db_session, auth_headers):
        """Test marking already complete todo."""
        todo = Todo(
            user_id=test_user.id,
            title="Already Complete",
            is_completed=True
        )
        db_session.add(todo)
        db_session.commit()

        response = authenticated_client.patch(
            f'/api/todos/{todo.id}/complete',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_completed'] is True

    def test_mark_complete_not_found(self, authenticated_client, auth_headers):
        """Test 404 when marking non-existent todo as complete."""
        response = authenticated_client.patch(
            '/api/todos/non-existent-id/complete',
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_mark_complete_other_users_todo(self, authenticated_client, test_user_2, db_session, auth_headers):
        """Test that users cannot mark other users' todos as complete."""
        todo = Todo(
            user_id=test_user_2.id,
            title="Other User's Todo",
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        response = authenticated_client.patch(
            f'/api/todos/{todo.id}/complete',
            headers=auth_headers
        )
        assert response.status_code == 404


class TestMarkIncomplete:
    """Tests for PATCH /api/todos/{id}/incomplete endpoint."""

    def test_mark_incomplete_success(self, authenticated_client, test_user, db_session, auth_headers):
        """Test successfully marking todo as incomplete."""
        todo = Todo(
            user_id=test_user.id,
            title="Complete Todo",
            is_completed=True
        )
        db_session.add(todo)
        db_session.commit()

        response = authenticated_client.patch(
            f'/api/todos/{todo.id}/incomplete',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_completed'] is False
        assert data['data']['completed_at'] is None

    def test_mark_incomplete_already_incomplete(self, authenticated_client, test_user, db_session, auth_headers):
        """Test marking already incomplete todo."""
        todo = Todo(
            user_id=test_user.id,
            title="Already Incomplete",
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        response = authenticated_client.patch(
            f'/api/todos/{todo.id}/incomplete',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['is_completed'] is False


class TestGetStats:
    """Tests for GET /api/todos/stats endpoint."""

    def test_get_stats_success(self, authenticated_client, test_user, db_session):
        """Test successful retrieval of todo statistics."""
        # Create todos with different states
        todo1 = Todo(user_id=test_user.id, title="Todo 1", is_completed=False, priority=PriorityLevel.HIGH.value)
        todo2 = Todo(user_id=test_user.id, title="Todo 2", is_completed=True, priority=PriorityLevel.MEDIUM.value)
        todo3 = Todo(user_id=test_user.id, title="Todo 3", is_completed=True, priority=PriorityLevel.LOW.value)
        db_session.add_all([todo1, todo2, todo3])
        db_session.commit()

        response = authenticated_client.get('/api/todos/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['total'] == 3
        assert data['data']['completed'] == 2
        assert data['data']['pending'] == 1
        assert data['data']['completion_rate'] == pytest.approx(66.67, rel=0.1)
        assert 'by_priority' in data['data']

    def test_get_stats_empty(self, authenticated_client):
        """Test stats when user has no todos."""
        response = authenticated_client.get('/api/todos/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['total'] == 0
        assert data['data']['completion_rate'] == 0.0

    def test_get_stats_unauthorized(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.get('/api/todos/stats')
        assert response.status_code == 401


class TestBulkUpdate:
    """Tests for POST /api/todos/bulk endpoint."""

    def test_bulk_update_complete(self, authenticated_client, test_user, db_session, auth_headers):
        """Test bulk marking todos as complete."""
        todo1 = Todo(user_id=test_user.id, title="Todo 1", is_completed=False)
        todo2 = Todo(user_id=test_user.id, title="Todo 2", is_completed=False)
        db_session.add_all([todo1, todo2])
        db_session.commit()

        payload = {
            'ids': [todo1.id, todo2.id],
            'is_completed': True
        }
        response = authenticated_client.post(
            '/api/todos/bulk',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['updated_count'] == 2

    def test_bulk_update_priority(self, authenticated_client, test_user, db_session, auth_headers):
        """Test bulk updating priority."""
        todo1 = Todo(user_id=test_user.id, title="Todo 1", priority=PriorityLevel.LOW.value)
        todo2 = Todo(user_id=test_user.id, title="Todo 2", priority=PriorityLevel.MEDIUM.value)
        db_session.add_all([todo1, todo2])
        db_session.commit()

        payload = {
            'ids': [todo1.id, todo2.id],
            'priority': 'high'
        }
        response = authenticated_client.post(
            '/api/todos/bulk',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_bulk_update_other_users_todos(self, authenticated_client, test_user, test_user_2, db_session, auth_headers):
        """Test that bulk update only affects current user's todos."""
        todo1 = Todo(user_id=test_user.id, title="User 1 Todo", is_completed=False)
        todo2 = Todo(user_id=test_user_2.id, title="User 2 Todo", is_completed=False)
        db_session.add_all([todo1, todo2])
        db_session.commit()

        payload = {
            'ids': [todo1.id, todo2.id],
            'is_completed': True
        }
        response = authenticated_client.post(
            '/api/todos/bulk',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        # Should only update the user's own todo
        assert data['data']['updated_count'] == 1

    def test_bulk_update_empty_ids(self, authenticated_client, auth_headers):
        """Test bulk update with empty ids list."""
        payload = {
            'ids': [],
            'is_completed': True
        }
        response = authenticated_client.post(
            '/api/todos/bulk',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['updated_count'] == 0


class TestClearCompleted:
    """Tests for DELETE /api/todos/completed endpoint."""

    def test_clear_completed_success(self, authenticated_client, test_user, db_session, auth_headers):
        """Test successfully clearing all completed todos."""
        todo1 = Todo(user_id=test_user.id, title="Active", is_completed=False)
        todo2 = Todo(user_id=test_user.id, title="Completed 1", is_completed=True)
        todo3 = Todo(user_id=test_user.id, title="Completed 2", is_completed=True)
        db_session.add_all([todo1, todo2, todo3])
        db_session.commit()

        response = authenticated_client.delete(
            '/api/todos/completed',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['deleted_count'] == 2

        # Verify only active todo remains
        remaining = db_session.query(Todo).filter_by(user_id=test_user.id).all()
        assert len(remaining) == 1
        assert remaining[0].title == "Active"

    def test_clear_completed_none_exist(self, authenticated_client, test_user, db_session, auth_headers):
        """Test clearing when no completed todos exist."""
        todo = Todo(user_id=test_user.id, title="Active", is_completed=False)
        db_session.add(todo)
        db_session.commit()

        response = authenticated_client.delete(
            '/api/todos/completed',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['deleted_count'] == 0

    def test_clear_completed_other_users_todos(self, authenticated_client, test_user, test_user_2, db_session, auth_headers):
        """Test that clearing only affects current user's todos."""
        todo1 = Todo(user_id=test_user.id, title="User 1 Completed", is_completed=True)
        todo2 = Todo(user_id=test_user_2.id, title="User 2 Completed", is_completed=True)
        db_session.add_all([todo1, todo2])
        db_session.commit()

        response = authenticated_client.delete(
            '/api/todos/completed',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['deleted_count'] == 1

        # Verify other user's todo still exists
        other_todo = db_session.get(Todo, todo2.id)
        assert other_todo is not None


class TestBulkDelete:
    """Tests for POST /api/todos/bulk-delete endpoint."""

    def test_bulk_delete_success(self, authenticated_client, test_user, db_session, auth_headers):
        """Test successfully deleting multiple todos."""
        todo1 = Todo(user_id=test_user.id, title="Todo 1", is_completed=False)
        todo2 = Todo(user_id=test_user.id, title="Todo 2", is_completed=False)
        todo3 = Todo(user_id=test_user.id, title="Todo 3", is_completed=False)
        db_session.add_all([todo1, todo2, todo3])
        db_session.commit()

        payload = {'ids': [todo1.id, todo2.id]}
        response = authenticated_client.post(
            '/api/todos/bulk-delete',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['deleted_count'] == 2

        # Verify remaining todo
        remaining = db_session.query(Todo).filter_by(user_id=test_user.id).all()
        assert len(remaining) == 1
        assert remaining[0].title == "Todo 3"

    def test_bulk_delete_other_users_todos(self, authenticated_client, test_user, test_user_2, db_session, auth_headers):
        """Test that bulk delete only affects current user's todos."""
        todo1 = Todo(user_id=test_user.id, title="User 1 Todo", is_completed=False)
        todo2 = Todo(user_id=test_user_2.id, title="User 2 Todo", is_completed=False)
        db_session.add_all([todo1, todo2])
        db_session.commit()

        payload = {'ids': [todo1.id, todo2.id]}
        response = authenticated_client.post(
            '/api/todos/bulk-delete',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['deleted_count'] == 1

        # Verify other user's todo still exists
        other_todo = db_session.get(Todo, todo2.id)
        assert other_todo is not None

    def test_bulk_delete_empty_ids(self, authenticated_client, auth_headers):
        """Test bulk delete with empty ids list."""
        payload = {'ids': []}
        response = authenticated_client.post(
            '/api/todos/bulk-delete',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['deleted_count'] == 0

    def test_bulk_delete_missing_body(self, authenticated_client, auth_headers):
        """Test bulk delete with missing request body."""
        response = authenticated_client.post(
            '/api/todos/bulk-delete',
            headers=auth_headers
        )
        assert response.status_code == 400


class TestTodoEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_todo_title_boundary_min(self, authenticated_client, auth_headers):
        """Test creating todo with minimum valid title length."""
        payload = {'title': 'A'}  # Single character
        response = authenticated_client.post(
            '/api/todos',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 201

    def test_todo_title_boundary_max(self, authenticated_client, auth_headers):
        """Test creating todo with maximum valid title length."""
        payload = {'title': 'A' * 200}  # Assuming max is 200
        response = authenticated_client.post(
            '/api/todos',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 201

    def test_todo_description_boundary_max(self, authenticated_client, auth_headers):
        """Test creating todo with maximum valid description length."""
        payload = {
            'title': 'Test',
            'description': 'A' * 2000  # Assuming max is 2000
        }
        response = authenticated_client.post(
            '/api/todos',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 201

    def test_todo_pagination_bounds(self, authenticated_client, test_user, db_session):
        """Test pagination with boundary values."""
        # Test per_page=1 (minimum)
        todo = Todo(user_id=test_user.id, title="Todo", is_completed=False)
        db_session.add(todo)
        db_session.commit()

        response = authenticated_client.get('/api/todos?per_page=1')
        assert response.status_code == 200

    def test_todo_pagination_max_per_page(self, authenticated_client, test_user, db_session):
        """Test pagination with max per_page value."""
        response = authenticated_client.get('/api/todos?per_page=100')
        assert response.status_code == 200

    def test_todo_invalid_priority(self, authenticated_client, auth_headers):
        """Test creating todo with invalid priority value."""
        payload = {
            'title': 'Test',
            'priority': 'invalid_priority'
        }
        response = authenticated_client.post(
            '/api/todos',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_todo_invalid_due_date(self, authenticated_client, auth_headers):
        """Test creating todo with invalid due date format."""
        payload = {
            'title': 'Test',
            'due_date': 'not-a-date'
        }
        response = authenticated_client.post(
            '/api/todos',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_todo_special_characters_in_title(self, authenticated_client, auth_headers):
        """Test creating todo with special characters in title."""
        payload = {
            'title': 'Test @#$%^&*()_+-=[]{}|;\':",./<>?'
        }
        response = authenticated_client.post(
            '/api/todos',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 201

    def test_todo_unicode_in_title(self, authenticated_client, auth_headers):
        """Test creating todo with unicode characters in title."""
        payload = {
            'title': 'Test 日本語 🎉 Ñoño'
        }
        response = authenticated_client.post(
            '/api/todos',
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 201


class TestTodoOptimisticConcurrency:
    """Tests for optimistic concurrency scenarios."""

    def test_concurrent_updates_last_write_wins(self, authenticated_client, test_user, db_session, auth_headers):
        """Test that last update wins in concurrent scenario."""
        todo = Todo(
            user_id=test_user.id,
            title="Original",
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        # First update
        response1 = authenticated_client.patch(
            f'/api/todos/{todo.id}',
            json={'title': 'First Update'},
            headers=auth_headers
        )
        assert response1.status_code == 200

        # Second update (should succeed)
        response2 = authenticated_client.patch(
            f'/api/todos/{todo.id}',
            json={'title': 'Second Update'},
            headers=auth_headers
        )
        assert response2.status_code == 200
        data = response2.get_json()
        assert data['data']['title'] == 'Second Update'


class TestTodoFilteringCombinations:
    """Tests for combined filtering scenarios."""

    def test_filter_status_and_priority(self, authenticated_client, test_user, db_session):
        """Test filtering by both status and priority."""
        todo1 = Todo(
            user_id=test_user.id,
            title="Active High",
            priority=PriorityLevel.HIGH.value,
            is_completed=False
        )
        todo2 = Todo(
            user_id=test_user.id,
            title="Completed High",
            priority=PriorityLevel.HIGH.value,
            is_completed=True
        )
        todo3 = Todo(
            user_id=test_user.id,
            title="Active Low",
            priority=PriorityLevel.LOW.value,
            is_completed=False
        )
        db_session.add_all([todo1, todo2, todo3])
        db_session.commit()

        response = authenticated_client.get('/api/todos?status=active&priority=high')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['items']) == 1
        assert data['data']['items'][0]['title'] == "Active High"

    def test_filter_search_and_status(self, authenticated_client, test_user, db_session):
        """Test filtering by search and status."""
        todo1 = Todo(
            user_id=test_user.id,
            title="Shopping Active",
            is_completed=False
        )
        todo2 = Todo(
            user_id=test_user.id,
            title="Shopping Completed",
            is_completed=True
        )
        todo3 = Todo(
            user_id=test_user.id,
            title="Work Active",
            is_completed=False
        )
        db_session.add_all([todo1, todo2, todo3])
        db_session.commit()

        response = authenticated_client.get('/api/todos?search=shopping&status=active')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['items']) == 1
        assert data['data']['items'][0]['title'] == "Shopping Active"

    def test_filter_case_insensitive_search(self, authenticated_client, test_user, db_session):
        """Test that search is case insensitive."""
        todo = Todo(
            user_id=test_user.id,
            title="UPPERCASE TITLE",
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        response = authenticated_client.get('/api/todos?search=uppercase')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['items']) == 1

    def test_filter_search_in_description(self, authenticated_client, test_user, db_session):
        """Test searching in description field."""
        todo = Todo(
            user_id=test_user.id,
            title="Title",
            description="Search in description",
            is_completed=False
        )
        db_session.add(todo)
        db_session.commit()

        response = authenticated_client.get('/api/todos?search=description')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['items']) == 1

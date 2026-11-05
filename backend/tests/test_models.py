"""Unit tests for SQLAlchemy models."""

import pytest
from datetime import datetime, timezone
from werkzeug.security import check_password_hash

from backend.app.extensions import db
from backend.app.models import User, Todo, PriorityLevel


class TestUserModel:
    """Test cases for the User model."""
    
    def test_user_creation(self, app):
        """Test basic user creation with required fields."""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com'
            )
            user.set_password('TestPassword123!')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.is_active is True
            assert user.created_at is not None
            assert user.updated_at is not None
            
            # Cleanup
            db.session.delete(user)
            db.session.commit()
    
    def test_user_password_hashing(self, app):
        """Test that passwords are properly hashed."""
        with app.app_context():
            user = User(
                username='hashtest',
                email='hash@example.com'
            )
            password = 'MySecretPassword123!'
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Verify password is hashed
            assert user.password_hash != password
            assert user.password_hash.startswith('pbkdf2:sha256:') or user.password_hash.startswith('scrypt:')
            
            # Verify password checking works
            assert user.check_password(password) is True
            assert user.check_password('WrongPassword') is False
            
            # Cleanup
            db.session.delete(user)
            db.session.commit()
    
    def test_user_unique_constraints(self, app, test_user):
        """Test that username and email must be unique."""
        with app.app_context():
            # Try to create user with same username
            duplicate_user = User(
                username=test_user.username,
                email='different@example.com'
            )
            duplicate_user.set_password('Password123!')
            db.session.add(duplicate_user)
            
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()
            
            db.session.rollback()
            
            # Try to create user with same email
            duplicate_email = User(
                username='differentuser',
                email=test_user.email
            )
            duplicate_email.set_password('Password123!')
            db.session.add(duplicate_email)
            
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()
            
            db.session.rollback()
    
    def test_user_timestamps(self, app):
        """Test that timestamps are automatically set."""
        with app.app_context():
            before_create = datetime.now(timezone.utc)
            
            user = User(
                username='timetest',
                email='time@example.com'
            )
            user.set_password('Password123!')
            db.session.add(user)
            db.session.commit()
            
            assert user.created_at is not None
            assert user.updated_at is not None
            assert user.created_at >= before_create
            
            # Store original timestamps
            original_created = user.created_at
            original_updated = user.updated_at
            
            # Update the user
            user.email = 'updated@example.com'
            db.session.commit()
            
            # created_at should not change, updated_at should change
            assert user.created_at == original_created
            assert user.updated_at >= original_updated
            
            # Cleanup
            db.session.delete(user)
            db.session.commit()
    
    def test_user_to_dict(self, app):
        """Test user serialization to dictionary."""
        with app.app_context():
            user = User(
                username='dicttest',
                email='dict@example.com'
            )
            user.set_password('Password123!')
            db.session.add(user)
            db.session.commit()
            
            user_dict = user.to_dict()
            
            assert 'id' in user_dict
            assert 'username' in user_dict
            assert 'email' in user_dict
            assert 'is_active' in user_dict
            assert 'created_at' in user_dict
            assert 'updated_at' in user_dict
            assert 'password_hash' not in user_dict
            assert user_dict['username'] == 'dicttest'
            assert user_dict['email'] == 'dict@example.com'
            
            # Cleanup
            db.session.delete(user)
            db.session.commit()
    
    def test_user_flask_login_properties(self, app):
        """Test Flask-Login required properties."""
        with app.app_context():
            user = User(
                username='flasktest',
                email='flask@example.com'
            )
            user.set_password('Password123!')
            db.session.add(user)
            db.session.commit()
            
            assert user.is_authenticated is True
            assert user.is_anonymous is False
            assert user.get_id() == user.id
            
            # Cleanup
            db.session.delete(user)
            db.session.commit()
    
    def test_user_repr(self, app):
        """Test user string representation."""
        with app.app_context():
            user = User(
                username='reprtest',
                email='repr@example.com'
            )
            user.set_password('Password123!')
            db.session.add(user)
            db.session.commit()
            
            repr_str = repr(user)
            assert 'User' in repr_str
            assert user.id in repr_str
            assert 'reprtest' in repr_str
            
            # Cleanup
            db.session.delete(user)
            db.session.commit()


class TestTodoModel:
    """Test cases for the Todo model."""
    
    def test_todo_creation(self, app, test_user):
        """Test basic todo creation."""
        with app.app_context():
            user = User.query.get(test_user.id)
            
            todo = Todo(
                user_id=user.id,
                title='Test Todo',
                description='Test description',
                priority=PriorityLevel.MEDIUM.value
            )
            db.session.add(todo)
            db.session.commit()
            
            assert todo.id is not None
            assert todo.user_id == user.id
            assert todo.title == 'Test Todo'
            assert todo.description == 'Test description'
            assert todo.is_completed is False
            assert todo.priority == PriorityLevel.MEDIUM.value
            assert todo.created_at is not None
            assert todo.updated_at is not None
            
            # Cleanup
            db.session.delete(todo)
            db.session.commit()
    
    def test_todo_default_values(self, app, test_user):
        """Test todo default values."""
        with app.app_context():
            user = User.query.get(test_user.id)
            
            todo = Todo(
                user_id=user.id,
                title='Minimal Todo'
            )
            db.session.add(todo)
            db.session.commit()
            
            assert todo.is_completed is False
            assert todo.priority == PriorityLevel.MEDIUM.value
            assert todo.description is None
            assert todo.due_date is None
            assert todo.completed_at is None
            
            # Cleanup
            db.session.delete(todo)
            db.session.commit()
    
    def test_todo_mark_complete(self, app, test_user):
        """Test marking todo as complete."""
        with app.app_context():
            user = User.query.get(test_user.id)
            
            todo = Todo(
                user_id=user.id,
                title='Complete Test'
            )
            db.session.add(todo)
            db.session.commit()
            
            assert todo.is_completed is False
            assert todo.completed_at is None
            
            todo.mark_complete()
            db.session.commit()
            
            assert todo.is_completed is True
            assert todo.completed_at is not None
            
            # Cleanup
            db.session.delete(todo)
            db.session.commit()
    
    def test_todo_mark_incomplete(self, app, test_user):
        """Test marking todo as incomplete."""
        with app.app_context():
            user = User.query.get(test_user.id)
            
            todo = Todo(
                user_id=user.id,
                title='Incomplete Test',
                is_completed=True
            )
            todo.mark_complete()
            db.session.add(todo)
            db.session.commit()
            
            assert todo.is_completed is True
            assert todo.completed_at is not None
            
            todo.mark_incomplete()
            db.session.commit()
            
            assert todo.is_completed is False
            assert todo.completed_at is None
            
            # Cleanup
            db.session.delete(todo)
            db.session.commit()
    
    def test_todo_priority_levels(self, app, test_user):
        """Test all priority levels."""
        with app.app_context():
            user = User.query.get(test_user.id)
            
            priorities = [
                PriorityLevel.LOW.value,
                PriorityLevel.MEDIUM.value,
                PriorityLevel.HIGH.value
            ]
            
            todos = []
            for i, priority in enumerate(priorities):
                todo = Todo(
                    user_id=user.id,
                    title=f'Priority Test {i}',
                    priority=priority
                )
                db.session.add(todo)
                todos.append(todo)
            
            db.session.commit()
            
            for i, todo in enumerate(todos):
                assert todo.priority == priorities[i]
            
            # Cleanup
            for todo in todos:
                db.session.delete(todo)
            db.session.commit()
    
    def test_todo_to_dict(self, app, test_user):
        """Test todo serialization to dictionary."""
        with app.app_context():
            user = User.query.get(test_user.id)
            
            todo = Todo(
                user_id=user.id,
                title='Dict Test',
                description='Test description',
                priority=PriorityLevel.HIGH.value
            )
            db.session.add(todo)
            db.session.commit()
            
            todo_dict = todo.to_dict()
            
            assert 'id' in todo_dict
            assert 'user_id' in todo_dict
            assert 'title' in todo_dict
            assert 'description' in todo_dict
            assert 'is_completed' in todo_dict
            assert 'priority' in todo_dict
            assert 'due_date' in todo_dict
            assert 'created_at' in todo_dict
            assert 'updated_at' in todo_dict
            assert 'completed_at' in todo_dict
            
            assert todo_dict['title'] == 'Dict Test'
            assert todo_dict['description'] == 'Test description'
            assert todo_dict['priority'] == PriorityLevel.HIGH.value
            
            # Cleanup
            db.session.delete(todo)
            db.session.commit()
    
    def test_todo_repr(self, app, test_user):
        """Test todo string representation."""
        with app.app_context():
            user = User.query.get(test_user.id)
            
            todo = Todo(
                user_id=user.id,
                title='Representation Test'
            )
            db.session.add(todo)
            db.session.commit()
            
            repr_str = repr(todo)
            assert 'Todo' in repr_str
            assert todo.id in repr_str
            assert 'Representation Test' in repr_str
            
            # Cleanup
            db.session.delete(todo)
            db.session.commit()


class TestUserTodoRelationship:
    """Test cases for User-Todo relationships."""
    
    def test_user_todos_relationship(self, app, test_user):
        """Test that user can access their todos."""
        with app.app_context():
            user = User.query.get(test_user.id)
            
            # Create todos for the user
            todo1 = Todo(user_id=user.id, title='Todo 1')
            todo2 = Todo(user_id=user.id, title='Todo 2')
            db.session.add_all([todo1, todo2])
            db.session.commit()
            
            # Access todos through relationship
            user_todos = user.todos.all()
            assert len(user_todos) == 2
            assert todo1 in user_todos
            assert todo2 in user_todos
            
            # Cleanup
            db.session.delete(todo1)
            db.session.delete(todo2)
            db.session.commit()
    
    def test_todo_user_relationship(self, app, test_user):
        """Test that todo can access its user."""
        with app.app_context():
            user = User.query.get(test_user.id)
            
            todo = Todo(user_id=user.id, title='User Access Test')
            db.session.add(todo)
            db.session.commit()
            
            # Access user through relationship
            assert todo.user is not None
            assert todo.user.id == user.id
            assert todo.user.username == user.username
            
            # Cleanup
            db.session.delete(todo)
            db.session.commit()
    
    def test_cascade_delete_user_todos(self, app):
        """Test that deleting a user cascades to their todos."""
        with app.app_context():
            # Create a user with todos
            user = User(
                username='cascadetest',
                email='cascade@example.com'
            )
            user.set_password('Password123!')
            db.session.add(user)
            db.session.commit()
            
            todo1 = Todo(user_id=user.id, title='Cascade Todo 1')
            todo2 = Todo(user_id=user.id, title='Cascade Todo 2')
            db.session.add_all([todo1, todo2])
            db.session.commit()
            
            # Get todo IDs
            todo1_id = todo1.id
            todo2_id = todo2.id
            
            # Delete the user
            db.session.delete(user)
            db.session.commit()
            
            # Verify todos are also deleted
            assert Todo.query.get(todo1_id) is None
            assert Todo.query.get(todo2_id) is None
    
    def test_multiple_users_isolated_todos(self, app):
        """Test that users can only see their own todos."""
        with app.app_context():
            # Create two users
            user1 = User(username='user1', email='user1@example.com')
            user1.set_password('Password123!')
            user2 = User(username='user2', email='user2@example.com')
            user2.set_password('Password123!')
            db.session.add_all([user1, user2])
            db.session.commit()
            
            # Create todos for each user
            todo1 = Todo(user_id=user1.id, title='User 1 Todo')
            todo2 = Todo(user_id=user2.id, title='User 2 Todo')
            db.session.add_all([todo1, todo2])
            db.session.commit()
            
            # Verify isolation
            user1_todos = user1.todos.all()
            user2_todos = user2.todos.all()
            
            assert len(user1_todos) == 1
            assert len(user2_todos) == 1
            assert user1_todos[0].title == 'User 1 Todo'
            assert user2_todos[0].title == 'User 2 Todo'
            
            # Cleanup
            db.session.delete(user1)
            db.session.delete(user2)
            db.session.commit()


class TestModelEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_todo_title_not_allowed(self, app, test_user):
        """Test that empty todo title is not allowed."""
        with app.app_context():
            user = User.query.get(test_user.id)
            
            todo = Todo(user_id=user.id, title='')
            db.session.add(todo)
            
            # This should raise an error due to nullable=False
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()
    
    def test_long_todo_title(self, app, test_user):
        """Test todo with maximum length title."""
        with app.app_context():
            user = User.query.get(test_user.id)
            
            # Title at max length (200 chars)
            long_title = 'A' * 200
            todo = Todo(user_id=user.id, title=long_title)
            db.session.add(todo)
            db.session.commit()
            
            assert todo.title == long_title
            
            # Cleanup
            db.session.delete(todo)
            db.session.commit()
    
    def test_todo_with_due_date(self, app, test_user):
        """Test todo with due date."""
        with app.app_context():
            user = User.query.get(test_user.id)
            
            due_date = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
            todo = Todo(
                user_id=user.id,
                title='Due Date Test',
                due_date=due_date
            )
            db.session.add(todo)
            db.session.commit()
            
            assert todo.due_date == due_date
            
            # Cleanup
            db.session.delete(todo)
            db.session.commit()
    
    def test_user_without_todos(self, app):
        """Test user with no todos."""
        with app.app_context():
            user = User(
                username='notodos',
                email='notodos@example.com'
            )
            user.set_password('Password123!')
            db.session.add(user)
            db.session.commit()
            
            assert user.todos.all() == []
            assert user.todos.count() == 0
            
            # Cleanup
            db.session.delete(user)
            db.session.commit()

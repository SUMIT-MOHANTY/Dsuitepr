"""Pytest configuration and fixtures for backend tests."""

import pytest
import uuid
from datetime import datetime, timezone
from typing import Generator

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from backend.app import create_app
from backend.app.extensions import db, login_manager
from backend.app.models.user import User
from backend.app.models.todo import Todo, PriorityLevel


@pytest.fixture(scope='session')
def app() -> Generator[Flask, None, None]:
    """Create application for the tests session."""
    _app = create_app('testing')
    
    # Create all tables
    with _app.app_context():
        db.create_all()
    
    yield _app
    
    # Cleanup
    with _app.app_context():
        db.drop_all()


@pytest.fixture(scope='function')
def client(app: Flask) -> Generator:
    """Create a test client for the app."""
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='function')
def db_session(app: Flask) -> Generator:
    """Create a fresh database session for each test."""
    with app.app_context():
        # Start a transaction
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Create a session bound to the connection
        session = scoped_session(sessionmaker(bind=connection))
        
        # Replace the db session with our test session
        old_session = db.session
        db.session = session
        
        yield session
        
        # Cleanup
        session.remove()
        transaction.rollback()
        connection.close()
        db.session = old_session


@pytest.fixture(scope='function')
def test_user(db_session) -> User:
    """Create a test user."""
    user = User(
        id=str(uuid.uuid4()),
        username='testuser',
        email='test@example.com',
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    user.set_password('TestPassword123!')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope='function')
def test_user_2(db_session) -> User:
    """Create a second test user."""
    user = User(
        id=str(uuid.uuid4()),
        username='testuser2',
        email='test2@example.com',
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    user.set_password('TestPassword123!')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope='function')
def authenticated_client(client, test_user) -> Generator:
    """Create an authenticated test client."""
    # Login the test user
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'TestPassword123!'
    })
    assert response.status_code == 200
    yield client


@pytest.fixture(scope='function')
def auth_headers(authenticated_client) -> dict:
    """Get authentication headers for requests."""
    return {'Content-Type': 'application/json'}


@pytest.fixture(scope='function')
def test_todo(db_session, test_user) -> Todo:
    """Create a test todo item."""
    todo = Todo(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        title='Test Todo',
        description='Test description',
        is_completed=False,
        priority=PriorityLevel.MEDIUM.value,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(todo)
    db_session.commit()
    return todo


@pytest.fixture(scope='function')
def test_todos(db_session, test_user) -> list[Todo]:
    """Create multiple test todo items."""
    todos = []
    for i in range(5):
        todo = Todo(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            title=f'Test Todo {i}',
            description=f'Test description {i}',
            is_completed=i % 2 == 0,
            priority=PriorityLevel.LOW.value if i % 3 == 0 else PriorityLevel.MEDIUM.value if i % 3 == 1 else PriorityLevel.HIGH.value,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        todos.append(todo)
    
    db_session.add_all(todos)
    db_session.commit()
    return todos


@pytest.fixture(scope='function')
def csrf_token(client) -> str:
    """Get CSRF token for testing."""
    response = client.get('/api/auth/csrf')
    if response.status_code == 200:
        return response.json.get('csrf_token', '')
    return ''

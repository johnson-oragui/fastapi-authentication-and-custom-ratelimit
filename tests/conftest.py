from unittest.mock import AsyncMock, patch
import pytest
from uuid import uuid4
from fastapi import Request



@pytest.fixture
def mock_get_db():
    with patch("api.db.database.get_db", autospec=True) as mock_get_db:
        mock_get_db.return_value = AsyncMock()
        yield mock_get_db()

@pytest.fixture(scope="session")
def mock_database_instance():
    """
    Create a Database instance
    """
    with patch("api.v1.services.auth.auth_service", autospec=True) as mock_auth_service:
        yield mock_auth_service

@pytest.fixture
def mock_verify_jwt_token():
    with patch("api.v1.services.auth.auth_service.verify_jwt_token", autospec=True) as mock_verify_jwt_token:
        mock_verify_jwt_token.return_value = {"user_id": "123", "token_type": "access"}
        yield mock_verify_jwt_token

@pytest.fixture
def mock_request():
    request = AsyncMock(spec=Request)
    yield request

@pytest.fixture
def user_one():
    """
    Create user 1
    """
    user1 = {
            'id': str(uuid4()),
            'username': 'johnson1',
            'first_name': 'Johnson',
            'last_name': 'Oragui',
            'email': 'johnson1@gmail.com',
            'password': 'Johnson1234#',
            'idempotency_key': '1234567890'
        }
    yield user1

@pytest.fixture
def user_two():
    """
    Create user 2
    """
    user1 = {
            'id': str(uuid4()),
            'username': 'Benson',
            'first_name': 'Benson',
            'last_name': 'Ben',
            'email': 'Benson@gmail.com',
            'password': 'Johnson1234#',
            'confirm_password': 'Johnson1234#',
        }
    idempotency_key = '1134567890'
    yield user1

@pytest.fixture
def user_three():
    """
    Create user 3
    """
    user1 = {
            'id': str(uuid4()),
            'username': 'Jayson',
            'first_name': 'Jayson',
            'last_name': 'Jayson',
            'email': 'Jayson@gmail.com',
            'password': 'Jayson',
            'idempotency_key': '1224567890'
        }
    yield user1

@pytest.fixture
def user_one_no_id():
    """
    Create user 2
    """
    user1 = {
            'username': 'Jane',
            'first_name': 'Jane',
            'last_name': 'Jane',
            'email': 'Jane1@gmail.com',
            'password': 'Jane',
            'idempotency_key': '1233567890'
        }
    yield user1

@pytest.fixture
def user_two_no_id():
    """
    Create user 2
    """
    user1 = {
            'username': 'Bourne',
            'first_name': 'Bourne',
            'last_name': 'Bourne',
            'email': 'Bourne1@gmail.com',
            'password': 'Bourne',
            'idempotency_key': '1234557890'
        }
    yield user1

@pytest.fixture
def user_three_no_id():
    """
    Create user 3
    """
    user1 = {
            'username': 'Bourne',
            'first_name': 'Bourne',
            'last_name': 'Bourne',
            'email': 'Bourne1@gmail.com',
            'password': 'Bourne',
            'idempotency_key': '1234557890'
        }
    yield user1

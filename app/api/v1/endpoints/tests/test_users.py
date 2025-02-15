import pytest
from fastapi.testclient import TestClient
from app.api.v1.endpoints.tests.conftest import TEST_PASSWORD

pytestmark = pytest.mark.asyncio

async def test_register_user(test_client, test_db):
    user_data = {
        "email": "newuser@test.com",
        "password": TEST_PASSWORD,
        "firstName": "New",
        "lastName": "User",
        "role": "Trainee"
    }
    
    response = await test_client.post(
        "/api/v1/users/register",
        json=user_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert data["role"] == "Trainee"

async def test_login_user(test_client, test_db, sample_trainee):
    login_data = {
        "email": "trainee@test.com",
        "password": TEST_PASSWORD
    }
    
    response = await test_client.post(
        "/api/v1/users/login",
        json=login_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

async def test_get_current_user(test_client, trainee_token, sample_trainee):
    headers = {"Authorization": f"Bearer {trainee_token}"}
    response = await test_client.get(
        "/api/v1/users/me",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "trainee@test.com"
    assert data["role"] == "Trainee" 
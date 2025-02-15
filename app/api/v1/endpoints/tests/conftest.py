import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from httpx import AsyncClient, ASGITransport
from main import app
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.core.deps import get_db
import asyncio
from datetime import datetime, UTC
from typing import AsyncGenerator

TEST_PASSWORD = "testpassword123"
HASHED_TEST_PASSWORD = get_password_hash(TEST_PASSWORD)

@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncIOMotorClient, None]:
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME + "_test"]
    
    # Override the database dependency
    async def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield db
    
    await client.drop_database(settings.DATABASE_NAME + "_test")
    client.close()
    
    # Remove the override after the test
    app.dependency_overrides = {}

@pytest.fixture
async def test_client(test_db):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True
    ) as client:
        yield client

@pytest.fixture
def trainer_token(sample_trainer):
    return create_access_token(
        data={"sub": "trainer_id", "role": "Trainer"}
    )

@pytest.fixture
def trainee_token(sample_trainee):
    return create_access_token(
        data={"sub": "trainee_id", "role": "Trainee"}
    )

@pytest.fixture
async def sample_trainer(test_db):
    trainer_data = {
        "_id": "trainer_id",
        "email": "trainer@test.com",
        "password": HASHED_TEST_PASSWORD,
        "firstName": "Test",
        "lastName": "Trainer",
        "role": "Trainer",
        "createdAt": datetime.now(UTC)
    }
    await test_db.users.insert_one(trainer_data)
    return trainer_data

@pytest.fixture
async def sample_trainee(test_db):
    trainee_data = {
        "_id": "trainee_id",
        "email": "trainee@test.com",
        "password": HASHED_TEST_PASSWORD,
        "firstName": "Test",
        "lastName": "Trainee",
        "role": "Trainee",
        "createdAt": datetime.now(UTC)
    }
    await test_db.users.insert_one(trainee_data)
    return trainee_data

@pytest.fixture
async def sample_lesson(test_db, sample_trainer):
    lesson_data = {
        "_id": "lesson_id",
        "title": "Sample Lesson",
        "description": "Sample Description",
        "contentType": "Text",
        "textContent": "Sample content",
        "createdBy": "trainer_id",
        "createdAt": datetime.now(UTC)
    }
    await test_db.lessons.insert_one(lesson_data)
    return lesson_data 
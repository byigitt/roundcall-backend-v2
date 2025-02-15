import pytest
from datetime import datetime, UTC

pytestmark = pytest.mark.asyncio

async def test_create_lesson(test_client, test_db, trainer_token, sample_trainer):
    lesson_data = {
        "title": "Test Lesson",
        "description": "Test Description",
        "contentType": "Text",
        "textContent": "This is a test lesson content",
        "timeBased": 0
    }
    
    headers = {"Authorization": f"Bearer {trainer_token}"}
    response = await test_client.post(
        "/api/v1/lessons/",
        json=lesson_data,
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == lesson_data["title"]
    assert data["createdBy"] == "trainer_id"

@pytest.fixture
async def sample_lesson(test_db, sample_trainer):
    lesson_data = {
        "_id": "lesson_id",
        "title": "Sample Lesson",
        "description": "Sample Description",
        "contentType": "Text",
        "textContent": "Sample content",
        "createdBy": "trainer_id",
        "createdAt": datetime.utcnow()
    }
    await test_db.lessons.insert_one(lesson_data)
    return lesson_data

async def test_assign_lesson(test_client, test_db, trainer_token, sample_lesson, sample_trainee):
    headers = {"Authorization": f"Bearer {trainer_token}"}
    
    response = await test_client.post(
        "/api/v1/lessons/lesson_id/assign",
        json={"trainee_id": "trainee_id"},
        headers=headers
    )
    
    assert response.status_code == 200
    
    assigned = await test_db.assignedLessons.find_one({
        "lessonID": "lesson_id",
        "traineeID": "trainee_id"
    })
    assert assigned is not None
    assert assigned["status"] == "Assigned"

async def test_get_lessons(test_client, test_db, trainee_token, sample_lesson):
    # First assign the lesson to the trainee
    assigned_lesson = {
        "lessonID": "lesson_id",
        "traineeID": "trainee_id",
        "trainerID": "trainer_id",
        "status": "Assigned"
    }
    await test_db.assignedLessons.insert_one(assigned_lesson)
    
    headers = {"Authorization": f"Bearer {trainee_token}"}
    response = await test_client.get(
        "/api/v1/lessons/",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Sample Lesson" 
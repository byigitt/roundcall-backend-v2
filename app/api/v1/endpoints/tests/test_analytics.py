import pytest
from httpx import AsyncClient
from main import app
from datetime import datetime, UTC

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def sample_analytics(test_db, sample_lesson, sample_trainee):
    analytics_data = {
        "_id": "analytics_id",
        "trainerID": "trainer_id",
        "traineeID": "trainee_id",
        "lessonID": "lesson_id",
        "totalQuestions": 5,
        "correctAnswers": 4,
        "avgResponseTime": 45.5,
        "attempts": 1,
        "generatedAt": datetime.utcnow()
    }
    await test_db.analytics.insert_one(analytics_data)
    return analytics_data

async def test_get_lesson_analytics(test_client, test_db, trainer_token, sample_analytics):
    headers = {"Authorization": f"Bearer {trainer_token}"}
    response = await test_client.get(
        "/api/v1/analytics/lesson/lesson_id",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["totalQuestions"] == 5
    assert data[0]["correctAnswers"] == 4

async def test_get_lesson_progress(test_client, test_db, trainer_token, sample_lesson):
    # Create some assigned lessons with different statuses
    assigned_lessons = [
        {
            "lessonID": "lesson_id",
            "traineeID": "trainee1",
            "trainerID": "trainer_id",
            "status": "Completed"
        },
        {
            "lessonID": "lesson_id",
            "traineeID": "trainee2",
            "trainerID": "trainer_id",
            "status": "In Progress"
        },
        {
            "lessonID": "lesson_id",
            "traineeID": "trainee3",
            "trainerID": "trainer_id",
            "status": "Assigned"
        }
    ]
    
    await test_db.assignedLessons.insert_many(assigned_lessons)
    
    headers = {"Authorization": f"Bearer {trainer_token}"}
    response = await test_client.get(
        "/api/v1/analytics/lesson/lesson_id/progress",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["completed"] == 1
    assert data["inProgress"] == 1
    assert data["notStarted"] == 1
    assert data["completionRate"] == pytest.approx(33.33, rel=1e-2)

async def test_get_trainee_analytics(test_client, test_db, trainer_token, sample_analytics):
    headers = {"Authorization": f"Bearer {trainer_token}"}
    response = await test_client.get(
        "/api/v1/analytics/trainee/trainee_id",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["traineeID"] == "trainee_id"
    assert data[0]["totalQuestions"] == 5
    assert data[0]["correctAnswers"] == 4 
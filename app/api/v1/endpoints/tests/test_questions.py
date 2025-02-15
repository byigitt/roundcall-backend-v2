import pytest
from datetime import datetime, UTC

pytestmark = pytest.mark.asyncio

async def test_create_question(test_client, test_db, trainer_token, sample_lesson):
    question_data = {
        "lessonID": "lesson_id",
        "questionText": "Test Question",
        "options": {
            "A": "Option 1",
            "B": "Option 2",
            "C": "Option 3",
            "D": "Option 4"
        },
        "correctAnswer": "A",
        "timeLimit": 60
    }
    
    headers = {"Authorization": f"Bearer {trainer_token}"}
    response = await test_client.post(
        "/api/v1/questions/",
        json=question_data,
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["questionText"] == question_data["questionText"]
    assert data["correctAnswer"] == question_data["correctAnswer"]

@pytest.fixture
async def sample_question(test_db, sample_lesson):
    question_data = {
        "_id": "question_id",
        "lessonID": "lesson_id",
        "trainerID": "trainer_id",
        "questionText": "Sample Question",
        "options": {
            "A": "Option 1",
            "B": "Option 2",
            "C": "Option 3",
            "D": "Option 4"
        },
        "correctAnswer": "A",
        "timeLimit": 60,
        "createdAt": datetime.now(UTC)
    }
    await test_db.questions.insert_one(question_data)
    return question_data

async def test_get_lesson_questions(test_client, test_db, trainee_token, sample_question):
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
        "/api/v1/questions/lesson/lesson_id",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["questionText"] == "Sample Question"

async def test_answer_question(test_client, test_db, trainee_token, sample_question):
    # First assign the lesson to the trainee
    assigned_lesson = {
        "lessonID": "lesson_id",
        "traineeID": "trainee_id",
        "trainerID": "trainer_id",
        "status": "In Progress"
    }
    await test_db.assignedLessons.insert_one(assigned_lesson)
    
    answer_data = {
        "questionID": "question_id",
        "selectedAnswer": "A",
        "responseTime": 30
    }
    
    headers = {"Authorization": f"Bearer {trainee_token}"}
    response = await test_client.post(
        "/api/v1/questions/answer",
        json=answer_data,
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["isCorrect"] == True
    assert data["selectedAnswer"] == "A"
    
    # Check if analytics was created
    analytics = await test_db.analytics.find_one({
        "traineeID": "trainee_id",
        "lessonID": "lesson_id"
    })
    assert analytics is not None
    assert analytics["correctAnswers"] == 1 
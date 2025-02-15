from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.question import QuestionCreate, QuestionInDB, QuestionResponse, QuestionResult
from app.models.user import UserInDB, UserRole
from app.core.deps import get_current_user, get_db
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=QuestionInDB)
async def create_question(
    question: QuestionCreate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can create questions"
        )
    
    # Dersin var olduğunu kontrol et
    lesson = await db.lessons.find_one({"_id": question.lessonID})
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    db_question = {
        **question.dict(),
        "trainerID": current_user.id,
        "createdAt": datetime.utcnow()
    }
    
    result = await db.questions.insert_one(db_question)
    db_question["id"] = str(result.inserted_id)
    
    return QuestionInDB(**db_question)

@router.get("/lesson/{lesson_id}", response_model=List[QuestionInDB])
async def get_lesson_questions(
    lesson_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    # Dersin var olduğunu kontrol et
    lesson = await db.lessons.find_one({"_id": lesson_id})
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Eğer trainee ise, dersin kendisine atanmış olduğunu kontrol et
    if current_user.role == UserRole.TRAINEE:
        assigned = await db.assignedLessons.find_one({
            "lessonID": lesson_id,
            "traineeID": current_user.id
        })
        if not assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This lesson is not assigned to you"
            )
    
    questions = await db.questions.find({"lessonID": lesson_id}).to_list(length=None)
    return [QuestionInDB(**q) for q in questions]

@router.post("/answer", response_model=QuestionResult)
async def answer_question(
    response: QuestionResponse,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainees can answer questions"
        )
    
    # Soruyu bul
    question = await db.questions.find_one({"_id": response.questionID})
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Dersin atanmış olduğunu kontrol et
    assigned = await db.assignedLessons.find_one({
        "lessonID": question["lessonID"],
        "traineeID": current_user.id
    })
    if not assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This lesson is not assigned to you"
        )
    
    # Cevabı kontrol et
    is_correct = response.selectedAnswer == question["correctAnswer"]
    
    result = QuestionResult(
        questionID=response.questionID,
        isCorrect=is_correct,
        selectedAnswer=response.selectedAnswer,
        correctAnswer=question["correctAnswer"],
        responseTime=response.responseTime
    )
    
    # Analytics için veri kaydet
    analytics_data = {
        "trainerID": question["trainerID"],
        "traineeID": current_user.id,
        "lessonID": question["lessonID"],
        "totalQuestions": 1,
        "correctAnswers": 1 if is_correct else 0,
        "avgResponseTime": response.responseTime,
        "attempts": 1,
        "generatedAt": datetime.utcnow()
    }
    
    await db.analytics.insert_one(analytics_data)
    
    return result 
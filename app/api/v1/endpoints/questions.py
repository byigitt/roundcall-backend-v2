from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.deps import get_current_user, get_db
from app.models.user import UserInDB, UserRole
from app.models.question import QuestionCreate, QuestionInDB, QuestionAnswer, AnswerResponse
from typing import List
from datetime import datetime, UTC

router = APIRouter()

@router.post("/", response_model=QuestionInDB, status_code=status.HTTP_201_CREATED)
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
    
    # Dersin trainer'ı olduğunu kontrol et
    if lesson["createdBy"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add questions to your own lessons"
        )
    
    question_dict = {
        **question.model_dump(),
        "trainerID": current_user.id,
        "createdAt": datetime.now(UTC)
    }
    
    result = await db.questions.insert_one(question_dict)
    question_dict["id"] = str(result.inserted_id)
    
    return QuestionInDB(**question_dict)

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
    
    if current_user.role == UserRole.TRAINER:
        # Trainer sadece kendi derslerinin sorularını görebilir
        if lesson["createdBy"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view questions for your own lessons"
            )
    else:
        # Trainee sadece kendisine atanan derslerin sorularını görebilir
        assigned = await db.assignedLessons.find_one({
            "lessonID": lesson_id,
            "traineeID": current_user.id
        })
        if not assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view questions for lessons assigned to you"
            )
    
    questions = await db.questions.find({
        "lessonID": lesson_id
    }).to_list(length=None)
    
    return [QuestionInDB(**{**q, "id": str(q["_id"])}) for q in questions]

@router.post("/answer", response_model=AnswerResponse)
async def answer_question(
    answer: QuestionAnswer,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainees can answer questions"
        )
    
    # Sorunun var olduğunu kontrol et
    question = await db.questions.find_one({"_id": answer.questionID})
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
            detail="You can only answer questions for lessons assigned to you"
        )
    
    # Dersin durumunu kontrol et
    if assigned["status"] != "In Progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only answer questions for lessons in progress"
        )
    
    # Cevabı kontrol et
    is_correct = answer.selectedAnswer == question["correctAnswer"]
    
    # Analitiği güncelle
    analytics = await db.analytics.find_one({
        "traineeID": current_user.id,
        "lessonID": question["lessonID"]
    })
    
    if analytics:
        # Mevcut analitiği güncelle
        await db.analytics.update_one(
            {"_id": analytics["_id"]},
            {
                "$inc": {
                    "totalQuestions": 1,
                    "correctAnswers": 1 if is_correct else 0,
                    "attempts": 1
                },
                "$set": {
                    "avgResponseTime": (
                        (analytics["avgResponseTime"] * analytics["totalQuestions"] + answer.responseTime) /
                        (analytics["totalQuestions"] + 1)
                    )
                }
            }
        )
    else:
        # Yeni analitik oluştur
        analytics = {
            "traineeID": current_user.id,
            "trainerID": question["trainerID"],
            "lessonID": question["lessonID"],
            "totalQuestions": 1,
            "correctAnswers": 1 if is_correct else 0,
            "avgResponseTime": answer.responseTime,
            "attempts": 1,
            "generatedAt": datetime.now(UTC)
        }
        await db.analytics.insert_one(analytics)
    
    return {
        "isCorrect": is_correct,
        "selectedAnswer": answer.selectedAnswer,
        "correctAnswer": question["correctAnswer"]
    } 
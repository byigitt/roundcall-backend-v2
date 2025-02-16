from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_database
from app.models.user import UserInDB, UserRole
from app.core.deps import get_current_user
from app.core.config import settings
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, EmailStr

router = APIRouter()

class AssignLessonRequest(BaseModel):
    trainee_email: EmailStr
    lesson_id: str

@router.post("/assign", status_code=status.HTTP_201_CREATED)
async def assign_lesson(
    request: AssignLessonRequest,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Trainer'ın bir trainee'ye ders ataması için endpoint
    """
    # Trainer kontrolü
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can assign lessons"
        )

    # Trainee'yi email'e göre bul
    trainee = await db[settings.DATABASE_NAME]["users"].find_one({
        "email": request.trainee_email,
        "role": UserRole.TRAINEE
    })
    if not trainee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainee not found with this email"
        )

    # Dersin var olup olmadığını kontrol et
    lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({
        "_id": ObjectId(request.lesson_id)
    })
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # Dersin daha önce atanıp atanmadığını kontrol et
    existing_assignment = await db[settings.DATABASE_NAME]["assignedLessons"].find_one({
        "traineeID": str(trainee["_id"]),
        "lessonID": request.lesson_id
    })
    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This lesson is already assigned to this trainee"
        )

    # Yeni assignment oluştur
    new_assignment = {
        "traineeID": str(trainee["_id"]),
        "traineeEmail": request.trainee_email,
        "lessonID": request.lesson_id,
        "trainerID": str(current_user.id),
        "status": "Assigned",
        "startedAt": None,
        "completedAt": None,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }

    result = await db[settings.DATABASE_NAME]["assignedLessons"].insert_one(new_assignment)
    
    return {
        "id": str(result.inserted_id),
        "message": f"Lesson assigned successfully to {request.trainee_email}"
    }

@router.get("/my-lessons", response_model=List[Dict[str, Any]])
async def get_my_lessons(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Trainee'nin kendisine atanmış dersleri görüntülemesi için endpoint
    """
    try:
        # Trainee'ye atanmış dersleri bul
        assigned_lessons = await db[settings.DATABASE_NAME]["assignedLessons"].find({
            "traineeID": str(current_user.id)
        }).to_list(length=None)

        if not assigned_lessons:
            return []

        # Ders detaylarını çek
        result = []
        for assignment in assigned_lessons:
            lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({
                "_id": ObjectId(assignment["lessonID"])
            })

            if lesson:
                # Trainer bilgilerini çek
                trainer = await db[settings.DATABASE_NAME]["users"].find_one({
                    "_id": ObjectId(assignment["trainerID"])
                })

                trainer_name = f"{trainer['firstName']} {trainer['lastName']}" if trainer else "Unknown Trainer"

                result.append({
                    "id": str(assignment["_id"]),
                    "lessonId": str(lesson["_id"]),
                    "title": lesson["title"],
                    "description": lesson.get("description", ""),
                    "contentType": lesson["contentType"],
                    "status": assignment["status"],
                    "assignedBy": trainer_name,
                    "traineeEmail": assignment.get("traineeEmail", "Unknown Email"),
                    "startedAt": assignment.get("startedAt"),
                    "completedAt": assignment.get("completedAt"),
                    "progress": calculate_lesson_progress(assignment, lesson)
                })

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

def calculate_lesson_progress(assignment: dict, lesson: dict) -> float:
    """
    Dersin tamamlanma yüzdesini hesapla
    """
    if assignment["status"] == "Completed":
        return 100.0
    elif assignment["status"] == "Assigned":
        return 0.0
    elif assignment["status"] == "In Progress":
        # Burada daha detaylı bir hesaplama yapılabilir
        # Örneğin: Çözülen soru sayısı / Toplam soru sayısı
        return 50.0
    
    return 0.0 
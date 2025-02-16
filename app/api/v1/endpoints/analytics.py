from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.deps import get_current_user, get_db
from app.models.user import UserInDB, UserRole
from app.models.analytics import AnalyticsInDB, LessonProgress
from typing import List, Dict, Any
from datetime import datetime, timezone

router = APIRouter()

@router.get("/lesson/{lesson_id}", response_model=List[AnalyticsInDB])
async def get_lesson_analytics(
    lesson_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can view analytics"
        )
    
    # Dersin var olduğunu kontrol et
    lesson = await db.lessons.find_one({"_id": lesson_id})
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Dersin trainer'ı olduğunu kontrol et
    if lesson["createdBy"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view analytics for your own lessons"
        )
    
    analytics = await db.analytics.find({
        "lessonID": lesson_id
    }).to_list(length=None)
    
    return [AnalyticsInDB(**{**a, "id": str(a["_id"])}) for a in analytics]

@router.get("/lesson/{lesson_id}/progress", response_model=LessonProgress)
async def get_lesson_progress(
    lesson_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can view progress"
        )
    
    # Dersin var olduğunu kontrol et
    lesson = await db.lessons.find_one({"_id": lesson_id})
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Dersin trainer'ı olduğunu kontrol et
    if lesson["createdBy"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view progress for your own lessons"
        )
    
    # Get all assigned lessons
    assigned_lessons = await db.assignedLessons.find({
        "lessonID": lesson_id
    }).to_list(length=None)
    
    total = len(assigned_lessons)
    completed = sum(1 for l in assigned_lessons if l["status"] == "Completed")
    in_progress = sum(1 for l in assigned_lessons if l["status"] == "In Progress")
    not_started = sum(1 for l in assigned_lessons if l["status"] == "Assigned")
    
    completion_rate = (completed / total * 100) if total > 0 else 0
    
    return {
        "total": total,
        "completed": completed,
        "inProgress": in_progress,
        "notStarted": not_started,
        "completionRate": completion_rate
    }

@router.get("/trainee/{trainee_id}", response_model=List[AnalyticsInDB])
async def get_trainee_analytics(
    trainee_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can view analytics"
        )
    
    # Trainee'nin var olduğunu kontrol et
    trainee = await db.users.find_one({"_id": trainee_id, "role": UserRole.TRAINEE})
    if not trainee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainee not found"
        )
    
    # Sadece kendi atadığın derslerin analitiğini görebilirsin
    
    analytics = await db.analytics.find({
        "traineeID": trainee_id,
        "trainerID": current_user.id
    }).to_list(length=None)
    
    return [AnalyticsInDB(**{**a, "id": str(a["_id"])}) for a in analytics] 
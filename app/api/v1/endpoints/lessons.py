from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.deps import get_current_user, get_db
from app.models.user import UserInDB, UserRole
from app.models.lesson import LessonCreate, LessonInDB, AssignedLesson, LessonWithProgress
from typing import List, Dict
from datetime import datetime, UTC
from app.core.config import settings
from bson import ObjectId

router = APIRouter()

@router.post("/", response_model=LessonInDB, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    lesson: LessonCreate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can create lessons"
        )
    
    lesson_dict = {
        **lesson.model_dump(),
        "createdBy": current_user.id,
        "createdAt": datetime.now(UTC)
    }
    
    result = await db[settings.DATABASE_NAME]["lessons"].insert_one(lesson_dict)
    created_lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({"_id": result.inserted_id})
    created_lesson["id"] = str(created_lesson["_id"])
    
    return LessonInDB(**created_lesson)

@router.get("", response_model=List[LessonInDB])
@router.get("/", response_model=List[LessonInDB])
async def get_lessons(
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role == UserRole.TRAINER:
        # Trainer kendi oluşturduğu dersleri görür
        lessons = await db[settings.DATABASE_NAME]["lessons"].find({
            "createdBy": current_user.id
        }).to_list(length=None)
    else:
        # Trainee kendisine atanan dersleri görür
        assigned_lessons = await db[settings.DATABASE_NAME]["assignedLessons"].find({
            "traineeID": current_user.id
        }).to_list(length=None)
        
        lesson_ids = [ObjectId(a["lessonID"]) for a in assigned_lessons]
        lessons = await db[settings.DATABASE_NAME]["lessons"].find({
            "_id": {"$in": lesson_ids}
        }).to_list(length=None)
    
    return [LessonInDB(**{**l, "id": str(l["_id"])}) for l in lessons]

@router.post("/{lesson_id}/assign", response_model=Dict[str, str])
async def assign_lesson(
    lesson_id: str,
    data: Dict[str, str],
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can assign lessons"
        )
    
    trainee_id = data.get("trainee_id")
    if not trainee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="trainee_id is required"
        )
    
    # Dersin var olduğunu kontrol et
    lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({"_id": ObjectId(lesson_id)})
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Dersin trainer'ı olduğunu kontrol et
    if lesson["createdBy"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only assign your own lessons"
        )
    
    # Trainee'nin var olduğunu kontrol et
    trainee = await db[settings.DATABASE_NAME]["users"].find_one({"_id": ObjectId(trainee_id), "role": UserRole.TRAINEE})
    if not trainee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainee not found"
        )
    
    # Dersin zaten atanmış olup olmadığını kontrol et
    existing_assignment = await db[settings.DATABASE_NAME]["assignedLessons"].find_one({
        "lessonID": ObjectId(lesson_id),
        "traineeID": ObjectId(trainee_id)
    })
    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lesson already assigned to this trainee"
        )
    
    assignment = {
        "lessonID": ObjectId(lesson_id),
        "traineeID": ObjectId(trainee_id),
        "trainerID": current_user.id,
        "status": "Assigned",
        "assignedAt": datetime.utcnow()
    }
    
    await db[settings.DATABASE_NAME]["assignedLessons"].insert_one(assignment)
    
    return {"message": "Lesson assigned successfully"}

@router.put("/{lesson_id}/status")
async def update_lesson_status(
    lesson_id: str,
    status: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainees can update lesson status"
        )
    
    assigned_lesson = await db[settings.DATABASE_NAME]["assignedLessons"].find_one({
        "lessonID": ObjectId(lesson_id),
        "traineeID": current_user.id
    })
    
    if not assigned_lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned lesson not found"
        )
    
    update_data = {"status": status}
    if status == "In Progress" and not assigned_lesson.get("startedAt"):
        update_data["startedAt"] = datetime.utcnow()
    elif status == "Completed":
        update_data["completedAt"] = datetime.utcnow()
    
    await db[settings.DATABASE_NAME]["assignedLessons"].update_one(
        {"_id": assigned_lesson["_id"]},
        {"$set": update_data}
    )
    
    return {"message": "Lesson status updated successfully"}

@router.put("/{lesson_id}", response_model=LessonInDB)
async def update_lesson(
    lesson_id: str,
    lesson_update: LessonCreate,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can update lessons"
        )
    
    # Dersin var olduğunu kontrol et
    existing_lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({"_id": ObjectId(lesson_id)})
    if not existing_lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Dersin trainer'ı olduğunu kontrol et
    if existing_lesson["createdBy"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own lessons"
        )
    
    # Dersi güncelle
    update_data = {
        **lesson_update.dict(),
        "updatedAt": datetime.utcnow()
    }
    
    await db[settings.DATABASE_NAME]["lessons"].update_one(
        {"_id": ObjectId(lesson_id)},
        {"$set": update_data}
    )
    
    # Güncellenmiş dersi getir
    updated_lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({"_id": ObjectId(lesson_id)})
    return LessonInDB(**updated_lesson) 
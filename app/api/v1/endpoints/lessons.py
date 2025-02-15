from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.lesson import LessonCreate, LessonInDB, AssignedLesson, LessonWithProgress
from app.models.user import UserInDB, UserRole
from app.core.deps import get_current_user, get_db
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=LessonInDB)
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
    
    db_lesson = {
        **lesson.dict(),
        "createdBy": current_user.id,
        "createdAt": datetime.utcnow()
    }
    
    result = await db.lessons.insert_one(db_lesson)
    db_lesson["id"] = str(result.inserted_id)
    
    return LessonInDB(**db_lesson)

@router.get("/", response_model=List[LessonWithProgress])
async def get_lessons(
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role == UserRole.TRAINER:
        # Trainer kendi oluşturduğu dersleri görür
        cursor = db.lessons.find({"createdBy": current_user.id})
    else:
        # Trainee kendisine atanan dersleri görür
        assigned = await db.assignedLessons.find(
            {"traineeID": current_user.id}
        ).to_list(length=None)
        
        lesson_ids = [a["lessonID"] for a in assigned]
        cursor = db.lessons.find({"_id": {"$in": lesson_ids}})
    
    lessons = await cursor.to_list(length=None)
    return [LessonWithProgress(**lesson) for lesson in lessons]

@router.post("/{lesson_id}/assign")
async def assign_lesson(
    lesson_id: str,
    trainee_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can assign lessons"
        )
    
    # Dersin var olduğunu kontrol et
    lesson = await db.lessons.find_one({"_id": lesson_id})
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Trainee'nin var olduğunu kontrol et
    trainee = await db.users.find_one({"_id": trainee_id, "role": UserRole.TRAINEE})
    if not trainee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainee not found"
        )
    
    assigned_lesson = {
        "lessonID": lesson_id,
        "traineeID": trainee_id,
        "trainerID": current_user.id,
        "status": "Assigned",
        "maxAttempts": 1
    }
    
    await db.assignedLessons.insert_one(assigned_lesson)
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
    
    assigned_lesson = await db.assignedLessons.find_one({
        "lessonID": lesson_id,
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
    
    await db.assignedLessons.update_one(
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
    existing_lesson = await db.lessons.find_one({"_id": lesson_id})
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
    
    await db.lessons.update_one(
        {"_id": lesson_id},
        {"$set": update_data}
    )
    
    # Güncellenmiş dersi getir
    updated_lesson = await db.lessons.find_one({"_id": lesson_id})
    return LessonInDB(**updated_lesson) 
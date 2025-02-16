from fastapi import APIRouter, Depends, HTTPException, status, Body
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.deps import get_current_user, get_db
from app.models.user import UserInDB, UserRole
from app.models.lesson import LessonCreate, LessonInDB, AssignedLesson, LessonWithProgress
from typing import List, Dict, Any
from datetime import datetime, UTC
from app.core.config import settings
from bson import ObjectId

router = APIRouter()

@router.post("", response_model=LessonInDB, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=LessonInDB, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    lesson: LessonCreate = Body(...),
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can create lessons"
        )
    
    # Convert questions to dict for MongoDB storage
    questions = [q.model_dump() for q in lesson.questions] if lesson.questions else []
    
    lesson_dict = {
        **lesson.model_dump(exclude={"questions"}),  # Exclude questions to handle them separately
        "questions": questions,  # Add converted questions
        "createdBy": str(current_user.id),
        "createdAt": datetime.now(UTC)
    }
    
    result = await db[settings.DATABASE_NAME]["lessons"].insert_one(lesson_dict)
    created_lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({"_id": result.inserted_id})
    
    return LessonInDB(**{**created_lesson, "id": str(created_lesson["_id"])})

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
    trainee_email = data.get("trainee_email")
    
    if not trainee_id and not trainee_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either trainee_id or trainee_email is required"
        )
    
    # Dersin var olduğunu kontrol et
    lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({"_id": ObjectId(lesson_id)})
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Dersin trainer'ı olduğunu kontrol et
    if str(lesson["createdBy"]) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only assign your own lessons"
        )
    
    # Trainee'yi bul (ID veya email ile)
    trainee_query = {"role": UserRole.TRAINEE}
    if trainee_id and ObjectId.is_valid(trainee_id):
        trainee_query["_id"] = ObjectId(trainee_id)
    elif trainee_email:
        trainee_query["email"] = trainee_email
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid trainee_id format and no trainee_email provided"
        )
    
    trainee = await db[settings.DATABASE_NAME]["users"].find_one(trainee_query)
    if not trainee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainee not found"
        )
    
    # Dersin zaten atanmış olup olmadığını kontrol et
    existing_assignment = await db[settings.DATABASE_NAME]["assignedLessons"].find_one({
        "lessonID": ObjectId(lesson_id),
        "traineeID": str(trainee["_id"])
    })
    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lesson already assigned to this trainee"
        )
    
    assignment = {
        "lessonID": ObjectId(lesson_id),
        "traineeID": str(trainee["_id"]),
        "trainerID": str(current_user.id),
        "status": "Assigned",
        "assignedAt": datetime.utcnow()
    }
    
    await db[settings.DATABASE_NAME]["assignedLessons"].insert_one(assignment)
    
    return {"message": f"Lesson assigned successfully to {trainee.get('email', 'trainee')}"}

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

@router.delete("/{lesson_id}", response_model=Dict[str, str])
async def delete_lesson(
    lesson_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can delete lessons"
        )
    
    # Check if lesson exists and belongs to the trainer
    lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({"_id": ObjectId(lesson_id)})
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    if str(lesson["createdBy"]) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own lessons"
        )
    
    # Delete the lesson
    delete_result = await db[settings.DATABASE_NAME]["lessons"].delete_one({"_id": ObjectId(lesson_id)})
    
    if delete_result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Also delete any assigned lessons
    await db[settings.DATABASE_NAME]["assignedLessons"].delete_many({"lessonID": lesson_id})
    
    return {"message": "Lesson deleted successfully"}

@router.delete("/assigned/{assigned_lesson_id}", response_model=Dict[str, str])
async def delete_assigned_lesson(
    assigned_lesson_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can unassign lessons"
        )
    
    try:
        # Check if assigned lesson exists
        assigned_lesson = await db[settings.DATABASE_NAME]["assignedLessons"].find_one({"_id": ObjectId(assigned_lesson_id)})
        
        if not assigned_lesson:
            # Try to find with string ID
            assigned_lesson = await db[settings.DATABASE_NAME]["assignedLessons"].find_one({"lessonID": assigned_lesson_id})
            if not assigned_lesson:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assigned lesson not found. Please check the ID."
                )
        
        # Check if the lesson belongs to the trainer
        lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({"_id": assigned_lesson["lessonID"]})
        if not lesson or str(lesson["createdBy"]) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only unassign your own lessons"
            )
        
        # Delete the assigned lesson
        delete_result = await db[settings.DATABASE_NAME]["assignedLessons"].delete_one({"_id": assigned_lesson["_id"]})
        
        if delete_result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not delete the assigned lesson"
            )
        
        return {"message": "Lesson unassigned successfully"}
        
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid lesson assignment ID format"
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error unassigning lesson: {str(e)}"
        )

@router.get("/assigned", response_model=List[AssignedLesson])
async def get_assigned_lessons(
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can view assigned lessons"
        )
    
    # Get all assigned lessons for lessons created by this trainer
    assigned_lessons = await db[settings.DATABASE_NAME]["assignedLessons"].find({
        "trainerID": str(current_user.id)
    }).to_list(length=None)
    
    return [
        AssignedLesson(**{
            **lesson,
            "id": str(lesson["_id"]),
            "lessonID": str(lesson["lessonID"])
        }) 
        for lesson in assigned_lessons
    ]

@router.get("/assigned/my-lessons", response_model=List[AssignedLesson])
async def get_my_assigned_lessons(
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainees can view their assigned lessons"
        )
    
    # Get all lessons assigned to this trainee
    assigned_lessons = await db[settings.DATABASE_NAME]["assignedLessons"].find({
        "traineeID": str(current_user.id)
    }).to_list(length=None)
    
    return [
        AssignedLesson(**{
            **lesson,
            "id": str(lesson["_id"]),
            "lessonID": str(lesson["lessonID"])
        }) 
        for lesson in assigned_lessons
    ]

@router.patch("/{lesson_id}", response_model=LessonInDB)
async def patch_lesson(
    lesson_id: str,
    lesson_update: Dict[str, Any] = Body(...),
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can update lessons"
        )
    
    # Check if lesson exists and belongs to the trainer
    existing_lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({"_id": ObjectId(lesson_id)})
    if not existing_lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    if str(existing_lesson["createdBy"]) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own lessons"
        )
    
    # Prepare update data
    update_data = {
        **lesson_update,
        "updatedAt": datetime.now(UTC)
    }
    
    # If questions are being updated, ensure they are in the correct format
    if "questions" in update_data:
        questions = update_data["questions"]
        update_data["questions"] = [
            {
                "questionText": q["questionText"],
                "options": [
                    {"text": opt["text"], "isCorrect": opt["isCorrect"]}
                    for opt in q["options"]
                ],
                "timeLimit": q.get("timeLimit")
            }
            for q in questions
        ]
    
    # Update the lesson
    await db[settings.DATABASE_NAME]["lessons"].update_one(
        {"_id": ObjectId(lesson_id)},
        {"$set": update_data}
    )
    
    # Get updated lesson
    updated_lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({"_id": ObjectId(lesson_id)})
    return LessonInDB(**{**updated_lesson, "id": str(updated_lesson["_id"])})

@router.patch("/assigned/{assigned_lesson_id}/progress", response_model=AssignedLesson)
async def update_assigned_lesson_progress(
    assigned_lesson_id: str,
    progress_data: Dict[str, Any] = Body(...),
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainees can update lesson progress"
        )
    
    try:
        # Check if assigned lesson exists and belongs to the trainee
        assigned_lesson = await db[settings.DATABASE_NAME]["assignedLessons"].find_one({
            "_id": ObjectId(assigned_lesson_id),
            "traineeID": str(current_user.id)
        })
        
        if not assigned_lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned lesson not found or you don't have access to it"
            )
        
        # Prepare update data
        update_data = {
            "status": progress_data.get("status", assigned_lesson.get("status")),
            "updatedAt": datetime.now(UTC)
        }
        
        # Add timestamps based on status
        if update_data["status"] == "In Progress" and not assigned_lesson.get("startedAt"):
            update_data["startedAt"] = datetime.now(UTC)
        elif update_data["status"] == "Completed" and not assigned_lesson.get("completedAt"):
            update_data["completedAt"] = datetime.now(UTC)
        
        # Update the assigned lesson
        await db[settings.DATABASE_NAME]["assignedLessons"].update_one(
            {"_id": ObjectId(assigned_lesson_id)},
            {"$set": update_data}
        )
        
        # Get updated assigned lesson
        updated_lesson = await db[settings.DATABASE_NAME]["assignedLessons"].find_one(
            {"_id": ObjectId(assigned_lesson_id)}
        )
        
        return AssignedLesson(**{
            **updated_lesson,
            "id": str(updated_lesson["_id"]),
            "lessonID": str(updated_lesson["lessonID"])
        })
        
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid assigned lesson ID format"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating lesson progress: {str(e)}"
        )

@router.get("/{lesson_id}", response_model=LessonInDB)
async def get_lesson(
    lesson_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    try:
        # Try to find the lesson
        lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({"_id": ObjectId(lesson_id)})
        
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        # If user is a trainee, check if they have access to this lesson
        if current_user.role == UserRole.TRAINEE:
            assigned_lesson = await db[settings.DATABASE_NAME]["assignedLessons"].find_one({
                "lessonID": ObjectId(lesson_id),
                "traineeID": str(current_user.id)
            })
            
            if not assigned_lesson:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this lesson"
                )
        # If user is a trainer, check if they created the lesson
        elif current_user.role == UserRole.TRAINER and str(lesson["createdBy"]) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own lessons"
            )
        
        return LessonInDB(**{**lesson, "id": str(lesson["_id"])})
        
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid lesson ID format"
            )
        raise e

@router.get("/assigned/{assigned_lesson_id}/details", response_model=LessonWithProgress)
async def get_assigned_lesson_details(
    assigned_lesson_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    try:
        # Get the assigned lesson
        assigned_lesson = await db[settings.DATABASE_NAME]["assignedLessons"].find_one({
            "_id": ObjectId(assigned_lesson_id)
        })
        
        if not assigned_lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned lesson not found"
            )
        
        # Check access rights
        if current_user.role == UserRole.TRAINEE and str(assigned_lesson["traineeID"]) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this lesson"
            )
        elif current_user.role == UserRole.TRAINER and str(assigned_lesson["trainerID"]) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own assigned lessons"
            )
        
        # Get the lesson details
        lesson = await db[settings.DATABASE_NAME]["lessons"].find_one({
            "_id": ObjectId(assigned_lesson["lessonID"])
        })
        
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        # Combine lesson and assignment data
        lesson_with_progress = {
            **lesson,
            "id": str(lesson["_id"]),
            "status": assigned_lesson["status"],
            "startedAt": assigned_lesson.get("startedAt"),
            "completedAt": assigned_lesson.get("completedAt"),
            "assignedAt": assigned_lesson["assignedAt"],
            "progress": 100 if assigned_lesson["status"] == "Completed" else (
                50 if assigned_lesson["status"] == "In Progress" else 0
            )
        }
        
        return LessonWithProgress(**lesson_with_progress)
        
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid assigned lesson ID format"
            )
        raise e 
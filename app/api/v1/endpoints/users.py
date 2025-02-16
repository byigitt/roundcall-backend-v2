from typing import Any, Dict, List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_database
from app.models.user import UserCreate, UserInDB, Token, UserLogin, UserRole
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password, get_password_hash
from app.core.deps import get_current_user, get_db
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.post("/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db=Depends(get_db)):
    # Email kontrolü
    existing_user = await db[settings.DATABASE_NAME]["users"].find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Kullanıcı oluşturma
    hashed_password = get_password_hash(user.password)
    db_user = {
        **user.model_dump(exclude={"password"}),
        "password": hashed_password,
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc)
    }
    
    result = await db[settings.DATABASE_NAME]["users"].insert_one(db_user)
    created_user = await db[settings.DATABASE_NAME]["users"].find_one({"_id": result.inserted_id})
    created_user["id"] = str(created_user["_id"])
    
    return UserInDB(**created_user)

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db=Depends(get_db)):
    user = await db[settings.DATABASE_NAME]["users"].find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Token oluşturma
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "role": user["role"]}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user["_id"])}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: UserInDB = Depends(get_current_user)):
    # Yeni token oluşturma
    access_token = create_access_token(
        data={"sub": current_user.id, "role": current_user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": current_user.id}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserInDB)
async def get_current_user(current_user: UserInDB = Depends(get_current_user)):
    try:
        return current_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/assigned-trainees", response_model=List[Dict[str, Any]])
async def get_all_assigned_trainees(
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainers can view assigned trainees"
        )
    
    # Trainer'ın atadığı tüm dersleri bul
    assigned_lessons = await db[settings.DATABASE_NAME]["assignedLessons"].find({
        "trainerID": current_user.id
    }).to_list(length=None)
    
    if not assigned_lessons:
        return []
    
    # Unique trainee ID'lerini topla
    trainee_ids = list(set(ObjectId(a["traineeID"]) for a in assigned_lessons))
    
    # Trainee bilgilerini çek
    trainees = await db[settings.DATABASE_NAME]["users"].find({
        "_id": {"$in": trainee_ids}
    }).to_list(length=None)
    
    # Her trainee için atanmış dersleri ve durumlarını topla
    result = []
    for trainee in trainees:
        trainee_assignments = [a for a in assigned_lessons if str(a["traineeID"]) == str(trainee["_id"])]
        
        # Her trainee için özet bilgileri hesapla
        total_lessons = len(trainee_assignments)
        completed_lessons = sum(1 for a in trainee_assignments if a["status"] == "Completed")
        in_progress_lessons = sum(1 for a in trainee_assignments if a["status"] == "In Progress")
        
        result.append({
            "id": str(trainee["_id"]),
            "email": trainee["email"],
            "firstName": trainee["firstName"],
            "lastName": trainee["lastName"],
            "totalAssignedLessons": total_lessons,
            "completedLessons": completed_lessons,
            "inProgressLessons": in_progress_lessons,
            "notStartedLessons": total_lessons - (completed_lessons + in_progress_lessons),
            "completionRate": round((completed_lessons / total_lessons * 100), 2) if total_lessons > 0 else 0
        })
    
    return result
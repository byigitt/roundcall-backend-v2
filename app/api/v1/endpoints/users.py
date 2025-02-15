from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_database
from app.models.user import UserCreate, UserInDB, Token, UserLogin
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password, get_password_hash
from app.core.deps import get_current_user, get_db
from datetime import datetime, timedelta, UTC

router = APIRouter()

@router.post("/", 
    response_model=UserInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    response_description="The created user"
)
async def create_user(
    user: UserCreate,
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Create a new user with the following information:

    - **username**: unique username for identification
    - **email**: unique email address
    - **password**: secure password
    - **full_name**: optional full name
    
    Returns the created user without the password hash.
    """
    # Check if user exists
    existing_user = await db[settings.DATABASE_NAME]["users"].find_one(
        {"$or": [{"username": user.username}, {"email": user.email}]}
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    user_dict = user.model_dump()
    result = await db[settings.DATABASE_NAME]["users"].insert_one(user_dict)
    created_user = await db[settings.DATABASE_NAME]["users"].find_one({"_id": result.inserted_id})
    return UserInDB(**created_user)

@router.post("/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db=Depends(get_db)):
    # Email kontrolü
    existing_user = await db.users.find_one({"email": user.email})
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
        "createdAt": datetime.now(UTC),
        "updatedAt": datetime.now(UTC)
    }
    
    result = await db.users.insert_one(db_user)
    db_user["id"] = str(result.inserted_id)
    
    return UserInDB(**db_user)

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db=Depends(get_db)):
    user = await db.users.find_one({"email": user_data.email})
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
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user 
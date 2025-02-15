from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_database
from app.models.user import UserCreate, UserInDB
from app.core.config import settings

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
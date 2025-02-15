from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_database
from app.models.user import UserCreate, UserInDB
from app.core.config import settings

router = APIRouter()

@router.post("/", response_model=UserInDB)
async def create_user(
    user: UserCreate,
    db: AsyncIOMotorClient = Depends(get_database)
):
    user_dict = user.model_dump()
    result = await db[settings.DATABASE_NAME]["users"].insert_one(user_dict)
    created_user = await db[settings.DATABASE_NAME]["users"].find_one({"_id": result.inserted_id})
    return UserInDB(**created_user) 
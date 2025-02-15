from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.config import settings
from app.core.security import SECRET_KEY, ALGORITHM
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_database
from app.models.user import UserInDB
from bson import ObjectId

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

async def get_db() -> AsyncIOMotorClient:
    return await get_database()

async def get_current_user(
    db: AsyncIOMotorClient = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> UserInDB:
    try:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        user = await db[settings.DATABASE_NAME]["users"].find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise credentials_exception
            
        user["id"] = str(user["_id"])
        return UserInDB(**user)
        
    except JWTError as e:
        raise credentials_exception
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.config import settings
from app.core.security import SECRET_KEY, ALGORITHM
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_database
from app.models.user import UserInDB

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

async def get_db() -> AsyncIOMotorClient:
    return await get_database()

async def get_current_user(
    db: AsyncIOMotorClient = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"_id": user_id})
    if user is None:
        raise credentials_exception
    
    user["id"] = str(user["_id"])
    return UserInDB(**user) 
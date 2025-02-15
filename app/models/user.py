from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    TRAINER = "Trainer"
    TRAINEE = "Trainee"

class UserBase(BaseModel):
    email: EmailStr
    firstName: str
    lastName: str
    role: UserRole
    department: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(UserBase):
    id: str
    createdAt: datetime
    updatedAt: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    exp: int
    role: UserRole 
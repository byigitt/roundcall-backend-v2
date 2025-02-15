from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ContentType(str, Enum):
    TEXT = "Text"
    VIDEO = "Video"
    BOTH = "Both"

class LessonBase(BaseModel):
    title: str
    description: Optional[str] = None
    contentType: ContentType
    textContent: Optional[str] = None
    videoURL: Optional[str] = None
    timeBased: Optional[int] = None

class LessonCreate(LessonBase):
    pass

class LessonInDB(LessonBase):
    id: str
    createdBy: str
    createdAt: datetime

class LessonStatus(str, Enum):
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"

class AssignedLesson(BaseModel):
    id: str
    lessonID: str
    traineeID: str
    trainerID: str
    status: LessonStatus
    startedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    maxAttempts: int = 1

class LessonWithProgress(LessonInDB):
    status: Optional[LessonStatus] = None
    progress: Optional[float] = None  # 0-100 arası yüzde
    startedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None 
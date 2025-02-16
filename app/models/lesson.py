from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ContentType(str, Enum):
    TEXT = "Text"
    VIDEO = "Video"
    BOTH = "Both"

class QuestionOption(BaseModel):
    text: str
    isCorrect: bool

class Question(BaseModel):
    questionText: str
    options: List[QuestionOption]
    timeLimit: Optional[int] = None

class LessonBase(BaseModel):
    title: str
    description: Optional[str] = None
    contentType: ContentType
    textContent: Optional[str] = None
    videoURL: Optional[str] = None
    timeBased: Optional[int] = None

class LessonCreate(LessonBase):
    questions: List[Question] = []

class LessonInDB(LessonBase):
    id: str
    createdBy: str
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    questions: List[Question] = []

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
    assignedAt: datetime

class LessonWithProgress(LessonInDB):
    status: Optional[LessonStatus] = None
    progress: Optional[float] = None  # 0-100 arası yüzde
    startedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    assignedAt: datetime 
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime

class QuestionBase(BaseModel):
    lessonID: str
    questionText: str
    options: Dict[str, str]  # {'A': 'Option 1', 'B': 'Option 2', ...}
    correctAnswer: str
    timeLimit: Optional[int] = None

class QuestionCreate(QuestionBase):
    pass

class QuestionInDB(QuestionBase):
    id: str
    trainerID: str
    createdAt: datetime

class QuestionResponse(BaseModel):
    questionID: str
    selectedAnswer: str
    responseTime: float  # saniye cinsinden

class QuestionResult(BaseModel):
    questionID: str
    isCorrect: bool
    selectedAnswer: str
    correctAnswer: str
    responseTime: float 
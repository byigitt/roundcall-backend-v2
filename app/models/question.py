from pydantic import BaseModel
from datetime import datetime
from typing import Dict

class QuestionBase(BaseModel):
    lessonID: str
    questionText: str
    options: Dict[str, str]  # {"A": "Option 1", "B": "Option 2", ...}
    correctAnswer: str
    timeLimit: int

class QuestionCreate(QuestionBase):
    pass

class QuestionInDB(QuestionBase):
    id: str
    trainerID: str
    createdAt: datetime

class QuestionAnswer(BaseModel):
    questionID: str
    selectedAnswer: str
    responseTime: float

class AnswerResponse(BaseModel):
    isCorrect: bool
    selectedAnswer: str
    correctAnswer: str 
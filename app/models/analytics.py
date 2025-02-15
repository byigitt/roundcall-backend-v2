from pydantic import BaseModel
from datetime import datetime

class AnalyticsBase(BaseModel):
    trainerID: str
    traineeID: str
    lessonID: str
    totalQuestions: int
    correctAnswers: int
    avgResponseTime: float
    attempts: int

class AnalyticsCreate(AnalyticsBase):
    pass

class AnalyticsInDB(AnalyticsBase):
    id: str
    generatedAt: datetime

class LessonProgress(BaseModel):
    total: int
    completed: int
    inProgress: int
    notStarted: int
    completionRate: float  # yüzde olarak 
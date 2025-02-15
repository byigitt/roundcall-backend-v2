from fastapi import APIRouter
from app.api.v1.endpoints import users, lessons, questions, analytics

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(lessons.router, prefix="/lessons", tags=["lessons"])
api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"]) 
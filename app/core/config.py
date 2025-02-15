from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "RoundCallv2"
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "roundcallv2"
    
    class Config:
        case_sensitive = True

settings = Settings()
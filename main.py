from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    RoundCall API documentation.
    
    ## Users
    You can:
    * Create users
    * Get user information
    * Update users
    * Delete users
    
    ## Authentication
    * JWT token authentication
    * OAuth2 with Password flow
    """,
    version="2.0.0",
    contact={
        "name": "Barış",
        "url": "https://github.com/byigitt/roundcall-backend-v2",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "users",
            "description": "Operations with users. The **login** logic is also here.",
        },
        {
            "name": "calls",
            "description": "Manage calls and call-related operations.",
        },
    ],
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.get("/", tags=["root"])
async def root():
    return {"message": "Welcome to RoundCall API"}

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
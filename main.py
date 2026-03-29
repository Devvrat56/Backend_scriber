import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import scribe_routes, chat_routes, history_routes
from core.config import settings

from db.session import init_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scribe_routes.router, prefix=settings.API_V1_STR)
app.include_router(chat_routes.router, prefix=settings.API_V1_STR)
app.include_router(history_routes.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    # Ensure upload directory exists
    if not os.path.exists(settings.UPLOAD_DIR):
        os.makedirs(settings.UPLOAD_DIR)
    
    # Initialize Database
    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")

@app.get("/")
async def root():
    return {"message": "Welcome to the Carelinq Unified Backend API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import auth, worker, tasks
from app.core.config import settings
from app.db.session import engine
from app import models

# Create all database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

# Configure CORS for Next.js frontend
import os
origins = ["http://localhost:3000", "http://localhost:3001"]
extra_origins = os.getenv("BACKEND_CORS_ORIGINS")
if extra_origins:
    origins.extend([o.strip() for o in extra_origins.split(",")])

print(f"[DEBUG] CORS origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(worker.router, prefix=f"{settings.API_V1_STR}/worker", tags=["worker"])
app.include_router(tasks.router, prefix=f"{settings.API_V1_STR}/tasks", tags=["tasks"])

@app.get("/")
def root():
    return {"message": "Welcome to TikTok Follow-for-Follow SaaS API"}

# Reload comment

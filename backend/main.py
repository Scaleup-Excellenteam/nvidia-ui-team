from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.routers import auth, docker, health
from app.database import engine
from app.models import Base

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ScaleUp-Nvidia UI Backend",
    description="Backend API for the ScaleUp-Nvidia container management platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(docker.router, prefix="/docker", tags=["Docker Management"])
app.include_router(health.router, prefix="/health", tags=["Health & Monitoring"])

@app.get("/")
async def root():
    return {"message": "ScaleUp-Nvidia UI Backend API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ui-backend"}

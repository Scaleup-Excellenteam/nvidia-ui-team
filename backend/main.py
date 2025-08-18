from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import time
import asyncio
import httpx

from app.routers import auth, docker, health
from app.database import engine, SessionLocal
from app.models import Base, User
from app.auth import get_password_hash

# Load environment variables
load_dotenv()

def create_tables():
    """Create database tables with retry logic for PostgreSQL"""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to database after {max_retries} attempts: {e}")
                raise

def ensure_admin_user():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@gmail.com").first()
        if not admin:
            user = User(
                email="admin@gmail.com",
                first_name="Admin",
                last_name="User",
                hashed_password=get_password_hash("admin"),  # lowercase password
                is_admin=True,
                is_active=True,
            )
            db.add(user)
            db.commit()
            print("Admin user created successfully")
        else:
            print("Admin user already exists")
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        db.close()

# Initialize database
create_tables()
ensure_admin_user()

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
    # Lightweight HTML landing similar to simple_server to make backend look nice again
    html = """
    <!doctype html>
    <html>
      <head>
        <meta charset='utf-8' />
        <meta name='viewport' content='width=device-width, initial-scale=1' />
        <title>ScaleUp-Nvidia Backend API</title>
        <style>
          body{font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;margin:0;padding:40px;background:#f7f7fb}
          .card{max-width:860px;margin:0 auto;background:#fff;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.08);overflow:hidden}
          .header{background:linear-gradient(135deg,#2c3e50,#34495e);color:#fff;padding:24px}
          .content{padding:24px}
          .tag{display:inline-block;padding:2px 8px;border-radius:999px;background:#eef2ff;color:#4338ca;font-weight:600;font-size:12px;margin-right:8px}
          a{color:#2563eb;text-decoration:none}
        </style>
      </head>
      <body>
        <div class='card'>
          <div class='header'>
            <h1 style='margin:0'>ScaleUp‑Nvidia Backend API</h1>
            <p style='opacity:.9;margin:8px 0 0'>FastAPI service for the UI platform</p>
          </div>
          <div class='content'>
            <p>
              <span class='tag'>FastAPI</span>
              <span class='tag'>PostgreSQL</span>
              <span class='tag'>JWT</span>
            </p>
            <p>Explore interactive docs at <a href='/docs'>/docs</a>.</p>
          </div>
        </div>
      </body>
    </html>
    """
    return Response(content=html, media_type="text/html", status_code=status.HTTP_200_OK)

# Service registry registration on startup
REGISTRY_BASE_URL = os.getenv("REGISTRY_BASE_URL", "http://127.0.0.1:7000")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
SERVICE_ID = os.getenv("SERVICE_ID", "ui-1")

@app.on_event("startup")
async def register_with_registry():
    payload = {
        "id": SERVICE_ID,
        "kind": "ui",
        "url": f"{PUBLIC_BASE_URL}/health",
        "status": "UP",
    }

    max_attempts = int(os.getenv("REGISTRY_RETRY_ATTEMPTS", "5"))
    retry_delay_seconds = float(os.getenv("REGISTRY_RETRY_DELAY", "2"))

    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{REGISTRY_BASE_URL}/registry/parts",
                    json=payload,
                    timeout=10,
                )
                resp.raise_for_status()
                print("Registered UI service with registry:", payload)
                break
        except Exception as e:
            if attempt < max_attempts - 1:
                print(
                    f"Registry registration failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                    f"Retrying in {retry_delay_seconds} seconds..."
                )
                await asyncio.sleep(retry_delay_seconds)
            else:
                print("Failed to register UI service with registry:", e)

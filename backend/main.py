from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.routers import auth, docker, health
from app.database import engine, SessionLocal
from app.models import Base, User
from app.auth import get_password_hash

# Load environment variables
load_dotenv()

# Create database tables and ensure admin user exists
Base.metadata.create_all(bind=engine)

def ensure_admin_user():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@gmail.com").first()
        if not admin:
            user = User(
                email="admin@gmail.com",
                first_name="Admin",
                last_name="User",
                hashed_password=get_password_hash("Admin"),
                is_admin=True,
                is_active=True,
            )
            db.add(user)
            db.commit()
    finally:
        db.close()

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
              <span class='tag'>SQLite</span>
              <span class='tag'>JWT</span>
            </p>
            <p>Explore interactive docs at <a href='/docs'>/docs</a>.</p>
          </div>
        </div>
      </body>
    </html>
    """
    return Response(content=html, media_type="text/html", status_code=status.HTTP_200_OK)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ui-backend"}

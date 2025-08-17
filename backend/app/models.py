from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DockerImage(Base):
    __tablename__ = "docker_images"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    image_file_path = Column(String, nullable=False)
    inner_port = Column(Integer, nullable=False)
    scaling_type = Column(String, nullable=False)  # "minimal", "maximal", "static"
    min_containers = Column(Integer, default=0)
    max_containers = Column(Integer, default=0)
    static_containers = Column(Integer, default=0)
    items_per_container = Column(Integer, nullable=False)
    payment_limit = Column(Float, default=0.0)
    description = Column(Text)
    status = Column(String, default="processing")  # "processing", "running", "stopped", "error"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

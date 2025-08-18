from pydantic import BaseModel, EmailStr, Field
from pydantic.config import ConfigDict
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")

    model_config = ConfigDict(populate_by_name=True)

class UserCreate(UserBase):
    password: str
    
    model_config = ConfigDict(populate_by_name=True)

class UserResponse(UserBase):
    id: int
    is_admin: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Docker Image schemas
class DockerImageBase(BaseModel):
    # Align field names with simple_server response via aliases
    name: str = Field(alias="image_name")
    inner_port: int = Field(alias="internal_port")
    scaling_type: str
    min_containers: Optional[int] = 0
    max_containers: Optional[int] = 0
    static_containers: Optional[int] = 0
    items_per_container: int
    payment_limit: float
    description: Optional[str] = None

class DockerImageCreate(DockerImageBase):
    pass

class DockerImageResponse(DockerImageBase):
    id: int
    user_id: int
    image_file_path: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class DockerImageUpdate(BaseModel):
    items_per_container: Optional[int] = Field(None, alias="itemRestrictions")
    payment_limit: Optional[float] = Field(None, alias="paymentLimit")

    model_config = ConfigDict(populate_by_name=True)

# Health schemas
class SystemComponent(BaseModel):
    name: str
    status: str  # "healthy", "warning", "error"
    uptime: str
    response_time: int

class SystemHealth(BaseModel):
    components: List[SystemComponent]

class BIMetrics(BaseModel):
    total_revenue: float
    total_customers: int
    active_images: int
    total_containers: int
    average_load: float

# External service schemas (for data from other teams)
class ContainerInstance(BaseModel):
    id: str
    status: str
    health: str
    cpu_usage: float
    memory_usage: float
    location: Optional[str] = None

class TrafficStats(BaseModel):
    requests_per_second: float
    total_requests: int
    average_response_time: float

class BillingInfo(BaseModel):
    total_cost: float
    breakdown: dict
    payment_limit: float
    current_payment: float
    remaining: float

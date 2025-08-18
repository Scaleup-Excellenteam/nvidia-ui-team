from pydantic import BaseModel, EmailStr, Field
from pydantic.config import ConfigDict
from typing import Optional, List,Literal,Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict,AliasChoices

ScalingType = Literal["static", "dynamic", "auto"]

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

class SignupResponse(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    model_config = ConfigDict(from_attributes=True)        

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

class DockerUploadResponse(BaseModel):
    image_name: str = Field(..., example="my-service")
    file_path: str = Field(..., example="/app/uploads/7_my-service.tar")
    inner_port: int = Field(..., example=8080)
    scaling_type: ScalingType = Field(..., example="static")
    min_containers: int = Field(..., example=0)
    max_containers: int = Field(..., example=0)
    static_containers: int = Field(..., example=1)
    items_per_container: int = Field(..., example=1000)
    payment_limit: float = Field(..., example=150.0)
    description: Optional[str] = Field(None, example="ETL pipeline for events")


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

class DockerImageListItem(BaseModel):
    id: int
    user_id: int
    user_email: Optional[EmailStr] = None
    image_name: str
    image_tag: str = Field(default="latest")
    internal_port: int               # שימי לב: internal_port (את ממפה מ-inner_port)
    running_containers: int
    total_containers: int
    requests_per_second: float
    total_requests: int
    total_cost: float
    cost_breakdown: Dict[str, float]
    healthy_containers: int
    total_errors: int
    payment_limit: float
    items_per_container: int
    status: Literal["processing", "ready", "failed"]

class DockerImagesResponse(BaseModel):
    images: List[DockerImageListItem]

class ImageRestrictionsUpdate(BaseModel):
    # מקבל גם camelCase מה-UI
    items_per_container: Optional[int] = Field(
        None, gt=0,
        validation_alias=AliasChoices("items_per_container", "itemRestrictions"),
    )
    payment_limit: Optional[float] = Field(
        None, ge=0,
        validation_alias=AliasChoices("payment_limit", "paymentLimit"),
    )

class ImageRestrictionsResponse(BaseModel):
    image_id: int = Field(..., serialization_alias="imageId")
    image_name: str = Field(..., serialization_alias="imageName")
    # מחזירים camelCase ב-JSON, שומרים snake_case בקוד/DB
    items_per_container: int = Field(..., serialization_alias="itemRestrictions")
    payment_limit: float = Field(..., serialization_alias="paymentLimit")
    status: Literal["processing", "ready", "failed"]
    updated_at: Optional[datetime] = Field(None, serialization_alias="updatedAt")

    # לאפשר החזרה מאובייקט ORM אם תרצי
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    
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

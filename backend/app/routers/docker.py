from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from app.database import get_db
from app.models import User, DockerImage
from app.schemas import DockerImagesResponse, DockerImageUpdate, DockerUploadResponse, ScalingType,DockerImageListItem,ImageRestrictionsUpdate, ImageRestrictionsResponse
from app.auth import get_current_active_user, get_current_admin_user
from app.external_services import external_client

router = APIRouter()

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/docker/upload", response_model=DockerUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_docker_image(
    image: UploadFile = File(...),
    image_name: str = Form(..., alias="imageName"),
    inner_port: int = Form(..., alias="innerPort"),
    scaling_type: ScalingType = Form(..., alias="scalingType"),
    min_containers: int = Form(0, alias="minContainers"),
    max_containers: int = Form(0, alias="maxContainers"),
    static_containers: int = Form(0, alias="staticContainers"),
    items_per_container: int = Form(..., alias="itemsPerContainer"),
    payment_limit: float = Form(..., alias="paymentLimit"),
    description: str | None = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a Docker image"""
    
    # Validate file type
    if not image.filename.endswith(('.tar', '.tar.gz', '.tgz')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Docker image files (.tar, .tar.gz, .tgz) are allowed"
        )
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{image.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # Create database record
    db_image = DockerImage(
        user_id=current_user.id,
        name=image_name,
        image_file_path=file_path,
        inner_port=inner_port,
        scaling_type=scaling_type,
        min_containers=min_containers,
        max_containers=max_containers,
        static_containers=static_containers,
        items_per_container=items_per_container,
        payment_limit=payment_limit,
        description=description,
        status="processing"
    )
    
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    # TODO: Send to orchestrator for processing
    # await external_client.start_container(str(db_image.id), count=1)
    
    return DockerUploadResponse(
        image_name=db_image.name,
        file_path=db_image.image_file_path,        # שימי לב: מיפוי לשם שהבטחת
        inner_port=db_image.inner_port,
        scaling_type=db_image.scaling_type,
        min_containers=db_image.min_containers or 0,
        max_containers=db_image.max_containers or 0,
        static_containers=db_image.static_containers or 0,
        items_per_container=db_image.items_per_container,
        payment_limit=db_image.payment_limit,
        description=db_image.description,
    )

@router.get("/images", response_model=DockerImagesResponse)
async def get_docker_images(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.is_admin:
        images = db.query(DockerImage).all()
    else:
        images = (
            db.query(DockerImage)
            .filter(DockerImage.user_id == current_user.id)
            .all()
        )

    items: List[DockerImageListItem] = []

    for image in images:
        try:
            instances_data = await external_client.get_container_instances(str(image.id))
            instance_list = instances_data.get("instances", [])
            total_containers = len(instance_list)
            running_containers = sum(1 for inst in instance_list if inst.get("status") == "running")

            healthy_containers = 0
            total_errors = 0
            for inst in instance_list:
                health = await external_client.get_container_health(inst.get("id"))
                if isinstance(health, dict) and health.get("status") == "healthy":
                    healthy_containers += 1
                errors = health.get("errors", []) if isinstance(health, dict) else []
                total_errors += len(errors)

            traffic_data = await external_client.get_traffic_stats(str(image.id))
            requests_per_second = traffic_data.get("requests_per_second", 0.0)
            total_requests = traffic_data.get("total_requests", 0)

            billing_data = await external_client.get_image_costs(str(image.id))
            total_cost = billing_data.get("total_cost", 0.0)
            cost_breakdown = billing_data.get("cost_breakdown", {})
            current_payment = billing_data.get("current_payment", total_cost)  # אם צריך
        except Exception:
            running_containers = 0
            total_containers = 0
            healthy_containers = 0
            total_errors = 0
            requests_per_second = 0.0
            total_requests = 0
            total_cost = 0.0
            current_payment = 0.0
            cost_breakdown = {}

        # מייל המשתמש (ל־admin)
        user_email = None
        try:
            u = db.query(User).filter(User.id == image.user_id).first()
            user_email = u.email if u else None
        except Exception:
            pass

        items.append(DockerImageListItem(
            id=image.id,
            user_id=image.user_id,
            user_email=user_email,
            image_name=image.name,
            image_tag="latest",
            internal_port=image.inner_port,              # מיפוי מ-inner_port
            running_containers=running_containers,
            total_containers=total_containers,
            requests_per_second=requests_per_second,
            total_requests=total_requests,
            total_cost=total_cost,
            cost_breakdown=cost_breakdown,
            healthy_containers=healthy_containers,
            total_errors=total_errors,
            payment_limit=image.payment_limit,
            items_per_container=image.items_per_container,
            status=image.status,
        ))

    return DockerImagesResponse(images=items)

@router.put(
    "/images/{image_id}/restrictions",
    response_model=ImageRestrictionsResponse,
    status_code=status.HTTP_200_OK,
)
async def update_image_restrictions(
    image_id: int,
    body: ImageRestrictionsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # 404 אם לא קיים
    image: DockerImage | None = db.query(DockerImage).filter(DockerImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # הרשאות: רק בעלים או אדמין
    if not current_user.is_admin and image.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this image")

    # אם לא נשלח שום שדה לעדכון
    if body.items_per_container is None and body.payment_limit is None:
        raise HTTPException(status_code=400, detail="Nothing to update")

    # עדכון השדות (רק מה שנשלח)
    if body.items_per_container is not None:
        image.items_per_container = body.items_per_container
    if body.payment_limit is not None:
        image.payment_limit = body.payment_limit

    db.add(image)
    db.commit()
    db.refresh(image)

    # החזרת תשובה לפי החוזה שביקשת (camelCase ב-JSON)
    return ImageRestrictionsResponse(
        image_id=image.id,
        image_name=image.name,
        items_per_container=image.items_per_container,
        payment_limit=image.payment_limit,
        status=image.status,
        updated_at=image.updated_at,  # אם קיים בעמודה; אחרת ישאיר None
    )
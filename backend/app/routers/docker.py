from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from app.database import get_db
from app.models import User, DockerImage
from app.schemas import DockerImageResponse, DockerImageUpdate
from app.auth import get_current_active_user, get_current_admin_user
from app.external_services import external_client

router = APIRouter()

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=dict)
async def upload_docker_image(
    image: UploadFile = File(...),
    image_name: str = Form(..., alias="imageName"),
    inner_port: int = Form(..., alias="innerPort"),
    scaling_type: str = Form(..., alias="scalingType"),
    min_containers: Optional[int] = Form(0, alias="minContainers"),
    max_containers: Optional[int] = Form(0, alias="maxContainers"),
    static_containers: Optional[int] = Form(0, alias="staticContainers"),
    items_per_container: int = Form(..., alias="itemsPerContainer"),
    payment_limit: float = Form(..., alias="paymentLimit"),
    description: Optional[str] = Form(None),
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
    
    return {
        "success": True,
        "message": "Docker image uploaded successfully",
        "imageId": str(db_image.id),
        "imageName": image_name,
        "status": "processing"
    }

@router.get("/images", response_model=dict)
async def get_docker_images(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all Docker images for the current user (or all if admin).

    Returns a response compatible with the simple_server contract to keep the UI stable.
    """

    if current_user.is_admin:
        images = db.query(DockerImage).all()
    else:
        images = db.query(DockerImage).filter(DockerImage.user_id == current_user.id).all()

    result: List[dict] = []
    for image in images:
        try:
            # Containers info
            instances_data = await external_client.get_container_instances(str(image.id))
            instance_list = instances_data.get("instances", [])
            total_containers = len(instance_list)
            running_containers = sum(1 for inst in instance_list if inst.get("status") == "running")

            # Health and errors per container
            healthy_containers = 0
            total_errors = 0
            for inst in instance_list:
                health = await external_client.get_container_health(inst.get("id"))
                if health and health.get("status") == "healthy":
                    healthy_containers += 1
                # Some backends may return errors inside health, otherwise expose 0
                errors = health.get("errors", []) if isinstance(health, dict) else []
                total_errors += len(errors)

            # Traffic stats
            traffic_data = await external_client.get_traffic_stats(str(image.id))
            requests_per_second = traffic_data.get("requests_per_second", 0.0)
            total_requests = traffic_data.get("total_requests", 0)

            # Billing
            billing_data = await external_client.get_image_costs(str(image.id))
            total_cost = billing_data.get("total_cost", 0.0)
            cost_breakdown = billing_data.get("cost_breakdown", {})
            current_payment = billing_data.get("current_payment", total_cost)

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

        # Get user email for admin view
        user_email = None
        try:
            user = db.query(User).filter(User.id == image.user_id).first()
            user_email = user.email if user else None
        except Exception:
            user_email = None

        # Build response matching simple_server keys
        result.append({
            "id": image.id,
            "user_id": image.user_id,
            "user_email": user_email,
            "image_name": image.name,
            "image_tag": "latest",
            "internal_port": image.inner_port,
            "running_containers": running_containers,
            "total_containers": total_containers,
            "requests_per_second": requests_per_second,
            "total_requests": total_requests,
            "total_cost": total_cost,
            "cost_breakdown": cost_breakdown,
            "healthy_containers": healthy_containers,
            "total_errors": total_errors,
            "payment_limit": image.payment_limit,
            "items_per_container": image.items_per_container,
            "status": image.status,
        })

    return {"images": result}

@router.put("/images/{image_id}/restrictions", response_model=dict)
async def update_image_restrictions(
    image_id: str,
    restrictions: DockerImageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update item restrictions for a Docker image"""
    
    # Get image
    image = db.query(DockerImage).filter(DockerImage.id == int(image_id)).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Check permissions (user can only update their own images, admin can update any)
    if not current_user.is_admin and image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this image"
        )
    
    # Update restrictions
    if restrictions.items_per_container is not None:
        image.items_per_container = restrictions.items_per_container
    
    if restrictions.payment_limit is not None:
        image.payment_limit = restrictions.payment_limit
    
    db.commit()
    
    # Update orchestrator resources
    try:
        await external_client.update_container_resources(
            image_id, 
            {"items_per_container": image.items_per_container}
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to update orchestrator resources: {e}")
    
    return {
        "success": True,
        "message": f"Item restrictions updated to {image.items_per_container}",
        "imageId": image_id,
        "itemRestrictions": image.items_per_container
    }

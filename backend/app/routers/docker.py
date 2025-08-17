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
    image_name: str = Form(...),
    inner_port: int = Form(...),
    scaling_type: str = Form(...),
    min_containers: Optional[int] = Form(0),
    max_containers: Optional[int] = Form(0),
    static_containers: Optional[int] = Form(0),
    items_per_container: int = Form(...),
    payment_limit: float = Form(...),
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

@router.get("/images", response_model=List[dict])
async def get_docker_images(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all Docker images for the current user (or all if admin)"""
    
    if current_user.is_admin:
        # Admin can see all images
        images = db.query(DockerImage).all()
    else:
        # Regular users see only their images
        images = db.query(DockerImage).filter(DockerImage.user_id == current_user.id).all()
    
    result = []
    for image in images:
        # Get additional data from external services
        try:
            # Get container instances from orchestrator
            instances_data = await external_client.get_container_instances(str(image.id))
            instances = len(instances_data.get("instances", []))
            
            # Get traffic stats from load balancer
            traffic_data = await external_client.get_traffic_stats(str(image.id))
            avg_requests = traffic_data.get("requests_per_second", 0.0)
            
            # Get billing info
            billing_data = await external_client.get_image_costs(str(image.id))
            cost = billing_data.get("total_cost", 0.0)
            payment = billing_data.get("current_payment", 0.0)
            
            # Get container health for errors
            health_data = await external_client.get_container_health(str(image.id))
            errors = health_data.get("errors", [])
            
        except Exception as e:
            # If external services are not available, use defaults
            instances = 0
            avg_requests = 0.0
            cost = 0.0
            payment = 0.0
            errors = []
        
        result.append({
            "id": str(image.id),
            "name": image.name,
            "instances": instances,
            "avgRequestsPerSecond": avg_requests,
            "cost": cost,
            "itemRestrictions": image.items_per_container,
            "paymentLimit": image.payment_limit,
            "errors": errors,
            "payment": payment,
            "status": image.status
        })
    
    return result

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

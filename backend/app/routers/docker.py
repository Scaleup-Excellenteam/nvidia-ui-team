from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime
from pathlib import Path

from app.logger import logger

from app.database import get_db
from app.models import User, DockerImage
from app.schemas import (
    DockerImagesResponse, 
    DockerImageUpdate, 
    DockerUploadResponse, 
    ScalingType,
    DockerImageListItem,
    ImageRestrictionsUpdate, 
    ImageRestrictionsResponse,
    StartContainersRequest,
    StartContainersResponse,
    StopAllContainersResponse,
    UpdateResourcesRequest,
    UpdateResourcesResponse,
)
from app.auth import get_current_active_user, get_current_admin_user
from app.external_services import external_client

router = APIRouter()

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=DockerUploadResponse, status_code=status.HTTP_201_CREATED)
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
    logger.info(f"POST /docker/upload - Docker image upload attempt by user: {current_user.email}, image_name: {image_name}")
    
    # Validate file type (case-insensitive)
    filename_lower = (image.filename or "").lower()
    if not filename_lower.endswith(('.tar', '.tar.gz', '.tgz')):
        logger.error(f"POST /docker/upload - Invalid file type: {image.filename}")
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
    
    logger.info(f"POST /docker/upload - Docker image uploaded successfully: {image_name}, ID: {db_image.id}")
    
    # Generate URL for the uploaded image
    image_filename = os.path.basename(db_image.image_file_path)
    base_url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    image_url = f"{base_url}/docker/images/{image_filename}"
    
    # Do not communicate with orchestrator on upload. Orchestrator integration happens on start/stop.
    
    return DockerUploadResponse(
        image_name=db_image.name,
        file_path=db_image.image_file_path,
        image_url=image_url,
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
    logger.info(f"GET /docker/images - Docker images requested by user: {current_user.email}")
    
    if current_user.is_admin:
        images = db.query(DockerImage).all()
        logger.info(f"GET /docker/images - Admin user requested all images, count: {len(images)}")
    else:
        images = (
            db.query(DockerImage)
            .filter(DockerImage.user_id == current_user.id)
            .all()
        )
        logger.info(f"GET /docker/images - Regular user requested their images, count: {len(images)}")

    items: List[DockerImageListItem] = []

    for image in images:
        try:
            instances_data = await external_client.get_container_instances(image.name)
            instance_list = instances_data.get("instances", [])
            total_containers = len(instance_list)
            running_containers = sum(1 for inst in instance_list if inst.get("status") == "running")

            # Fetch health once per image and aggregate
            health_data = await external_client.get_container_health(str(image.id))
            containers_health = health_data.get("containers", []) if isinstance(health_data, dict) else []
            healthy_containers = sum(
                1 for c in containers_health if isinstance(c, dict) and c.get("status") == "healthy"
            )
            total_errors = len(health_data.get("errors", [])) if isinstance(health_data, dict) else 0

            traffic_data = await external_client.get_traffic_stats(str(image.id))
            requests_per_second = traffic_data.get("requests_per_second", 0.0)
            total_requests = traffic_data.get("total_requests", 0)

            billing_data = await external_client.get_image_costs(str(image.id))
            total_cost = billing_data.get("total_cost", 0.0)
            cost_breakdown = billing_data.get("cost_breakdown", {})
            current_payment = billing_data.get("current_payment", total_cost)  # if needed
        except Exception as e:
            logger.error(f"GET /docker/images - Error fetching external data for image {image.id}: {e}")
            running_containers = 0
            total_containers = 0
            healthy_containers = 0
            total_errors = 0
            requests_per_second = 0.0
            total_requests = 0
            total_cost = 0.0
            current_payment = 0.0
            cost_breakdown = {}

        # User email (for admin)
        user_email = None
        try:
            u = db.query(User).filter(User.id == image.user_id).first()
            user_email = u.email if u else None
        except Exception as e:
            logger.error(f"GET /docker/images - Error fetching user email for image {image.id}: {e}")
            pass

        items.append(DockerImageListItem(
            id=image.id,
            user_id=image.user_id,
            user_email=user_email,
            image_name=image.name,
            image_tag="latest",
            internal_port=image.inner_port,              # mapping from inner_port
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

    logger.info(f"GET /docker/images - Successfully returned {len(items)} images")
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
    logger.info(f"PUT /docker/images/{image_id}/restrictions - Update attempt by user: {current_user.email}")
    
    # 404 if not exists
    image: DockerImage | None = db.query(DockerImage).filter(DockerImage.id == image_id).first()
    if not image:
        logger.error(f"PUT /docker/images/{image_id}/restrictions - Image not found")
        raise HTTPException(status_code=404, detail="Image not found")

    # Permissions: only owner or admin
    if not current_user.is_admin and image.user_id != current_user.id:
        logger.error(f"PUT /docker/images/{image_id}/restrictions - Unauthorized access attempt by user: {current_user.email}")
        raise HTTPException(status_code=403, detail="Not authorized to modify this image")

    # If no fields were sent for update
    if body.items_per_container is None and body.payment_limit is None:
        logger.error(f"PUT /docker/images/{image_id}/restrictions - No fields to update")
        raise HTTPException(status_code=400, detail="Nothing to update")

    # Update fields (only what was sent)
    if body.items_per_container is not None:
        image.items_per_container = body.items_per_container
    if body.payment_limit is not None:
        image.payment_limit = body.payment_limit

    db.add(image)
    db.commit()
    db.refresh(image)

    logger.info(f"PUT /docker/images/{image_id}/restrictions - Image restrictions updated successfully")

    # Return response according to the contract you requested (camelCase in JSON)
    return ImageRestrictionsResponse(
        image_id=image.id,
        image_name=image.name,
        items_per_container=image.items_per_container,
        payment_limit=image.payment_limit,
        status=image.status,
        updated_at=image.updated_at,  # if exists in column; otherwise will leave None
    )

@router.post("/images/{image_id}/start", response_model=StartContainersResponse)
async def start_image_containers(
    image_id: int,
    body: StartContainersRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    image: DockerImage | None = db.query(DockerImage).filter(DockerImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if not current_user.is_admin and image.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to start containers for this image")
    try:
        # Build orchestrator StartBody payload based on our stored upload metadata
        base_url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
        image_filename = os.path.basename(image.image_file_path)
        image_url = f"{base_url}/docker/images/{image_filename}"

        start_payload = {
            "image": f"{image.name}:latest",
            "image_url": image_url,
            "min_replicas": image.min_containers or 1,
            "max_replicas": image.max_containers or 5,
            "resources": {
                "cpu": "1.0",
                "memory": "512Mi",
            },
            "env": {},
            "ports": [{"container": image.inner_port, "host": image.inner_port}],
        }
        # Pass count for legacy compatibility if provided by UI
        if body.count is not None:
            start_payload["count"] = body.count

        result = await external_client.start_container(start_payload)
        started_ids = []
        if isinstance(result, dict):
            # Support both mock and real shapes
            if "started" in result and isinstance(result["started"], list):
                started_ids = result["started"]
            elif "container_id" in result and result.get("container_id"):
                started_ids = [str(result.get("container_id"))]

        return StartContainersResponse(started=started_ids)
    except Exception as e:
        logger.error(f"Failed to start containers for image {image_id}: {e}")
        raise

@router.post("/images/{image_id}/stop", response_model=StopAllContainersResponse)
async def stop_all_image_containers(
    image_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    image: DockerImage | None = db.query(DockerImage).filter(DockerImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if not current_user.is_admin and image.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to stop containers for this image")
    try:
        # In mocks we don't have a single call to stop all; iterate instances
        instances_data = await external_client.get_container_instances(str(image_id))
        instance_list = instances_data.get("instances", []) if isinstance(instances_data, dict) else []
        stopped: list[str] = []
        for inst in instance_list:
            inst_id = inst.get("id")
            if not inst_id:
                continue
            resp = await external_client.stop_container(str(image_id), inst_id)
            if resp.get("stopped"):
                stopped.append(inst_id)

        # Optionally notify orchestrator of desired state stop using the same body with count=0 if needed
        # (depends on orchestrator API semantics; keeping instance-level stops for now)
        return StopAllContainersResponse(stopped=stopped)
    except Exception as e:
        logger.error(f"Failed to stop containers for image {image_id}: {e}")
        raise

@router.put("/images/{image_id}/resources", response_model=UpdateResourcesResponse)
async def update_image_resources(
    image_id: int,
    body: UpdateResourcesRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    image: DockerImage | None = db.query(DockerImage).filter(DockerImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if not current_user.is_admin and image.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify resources for this image")
    resources: dict = {}
    if body.cpu_limit is not None:
        resources["cpu_limit"] = body.cpu_limit
    if body.memory_limit is not None:
        resources["memory_limit"] = body.memory_limit
    if not resources:
        raise HTTPException(status_code=400, detail="Nothing to update")
    try:
        result = await external_client.update_container_resources(str(image_id), resources)
        return UpdateResourcesResponse(updated=result.get("updated", []))
    except Exception as e:
        logger.error(f"Failed to update resources for image {image_id}: {e}")
        raise

@router.get("/images/{filename}")
async def get_image_file(filename: str):
    """Serve uploaded Docker image files with basic path traversal protection"""
    uploads_dir = Path(UPLOAD_DIR).resolve()
    requested_path = (uploads_dir / filename).resolve()

    # Ensure the requested file is within the uploads directory
    if not str(requested_path).startswith(str(uploads_dir)) or not requested_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(
        path=str(requested_path),
        filename=requested_path.name,
        media_type="application/octet-stream",
    )
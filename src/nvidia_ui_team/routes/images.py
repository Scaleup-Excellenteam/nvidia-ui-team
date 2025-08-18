from fastapi import APIRouter
from nvidia_ui_team.utils.consts import Routes
from nvidia_ui_team.models.outbound.images import OutbondImage
from uuid import UUID


class ImagesRouter:
    def __init__(self):
        self.router = APIRouter(prefix=Routes.IMAGES)

    def build(self):
        self.router.add_api_route("/{image_uuid}",
                                  self.get_images, methods=["GET"], response_model=OutbondImage)
        return self.router

    @staticmethod
    async def get_images(image_uuid: UUID):
        return {"message": "Hello, World!"}

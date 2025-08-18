from typing import Annotated
from pydantic import BaseModel, Field
from uuid import UUID


class OutbondImage(BaseModel):
    image_uuid: UUID
    image_name: str
    image_description: str | None = None
    internal_port: Annotated[int, Field(ge=1, le=65535)]

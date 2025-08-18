# nvidia_ui_team/models/outbound/user.py
from typing import Annotated
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


class OutboundUser(BaseModel):
    user_uuid: UUID
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True

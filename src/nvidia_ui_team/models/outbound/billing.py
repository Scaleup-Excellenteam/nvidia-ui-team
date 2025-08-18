# nvidia_ui_team/models/outbound/billing.py
from typing import Annotated
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime


class OutboundBilling(BaseModel):
    billing_uuid: UUID
    user_uuid: UUID  # מזהה המשתמש שהחשבונית שייכת לו
    amount: Annotated[float, Field(gt=0)]  # הסכום חייב להיות גדול מ-0
    description: str | None = None  # תיאור חיוב
    issued_at: datetime = Field(default_factory=datetime.utcnow)  # תאריך הפקת החשבונית
    due_date: date | None = None  # תאריך אחרון לתשלום
    is_paid: bool = False  # סטטוס תשלום

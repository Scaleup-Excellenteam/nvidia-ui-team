from fastapi import APIRouter
from nvidia_ui_team.utils.consts import Routes
from nvidia_ui_team.models.outbound.billing import OutboundBilling
from uuid import UUID


class BillingRouter:
    def __init__(self):
        self.router = APIRouter(prefix=Routes.BILLING)

    def build(self):
        self.router.add_api_route("/{bill_uuid}",
                                  self.get_bill, methods=["GET"], response_model=OutboundBilling)
        return self.router

    @staticmethod
    async def get_bill(bill_uuid: UUID):
        return {"id": bill_uuid, "amount": 199.99}

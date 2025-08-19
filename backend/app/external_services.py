import httpx
import os
from typing import List, Optional, Dict, Any
from fastapi import HTTPException

# Prefer in-repo mock services unless explicitly disabled
USE_MOCKS = os.getenv("USE_MOCK_SERVICES", "true").lower() in ("1", "true", "yes")
if USE_MOCKS:
    from mock_services import load_balancer as mock_lb  # type: ignore
    from mock_services import orchestrator as mock_orch  # type: ignore
    from mock_services import service_discovery as mock_sd  # type: ignore
    from mock_services import billing as mock_billing  # type: ignore

# External service URLs
ORCHESTRATOR_API_URL = os.getenv("ORCHESTRATOR_API_URL", "http://localhost:8001")
LOAD_BALANCER_API_URL = os.getenv("LOAD_BALANCER_API_URL", "http://localhost:8002")
SERVICE_DISCOVERY_API_URL = os.getenv("SERVICE_DISCOVERY_API_URL", "http://localhost:8003")
BILLING_API_URL = os.getenv("BILLING_API_URL", "http://localhost:8004")

class ExternalServiceClient:
    def __init__(self):
        self.orchestrator_url = ORCHESTRATOR_API_URL
        self.load_balancer_url = LOAD_BALANCER_API_URL
        self.service_discovery_url = SERVICE_DISCOVERY_API_URL
        self.billing_url = BILLING_API_URL

    async def _make_request(self, url: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Make HTTP request to external service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"External service error: {e}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"External service unavailable: {e}")

    # Orchestrator API calls
    async def get_container_instances(self, image_id: str) -> Dict[str, Any]:
        """Get all container instances for an image"""
        if USE_MOCKS:
            instances = mock_orch.get_containers_by_image(image_id)
            return {"instances": instances}  # keep dict with key 'instances'
        url = f"{self.orchestrator_url}/containers/{image_id}/instances"
        return await self._make_request(url)

    # Orchestrator DB image sync
    async def sync_image_to_orchestrator(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync an image to the orchestrator's database (for their images table)."""
        if USE_MOCKS:
            # In mocks, pretend success and echo minimal data
            return {"success": True, "image": image_data.get("image"), "url": image_data.get("image_url")}
        url = f"{self.orchestrator_url}/api/images"
        return await self._make_request(url, method="POST", json=image_data)

    async def start_container(self, image_id: str, count: int = 1, resources: Optional[Dict] = None) -> Dict[str, Any]:
        """Start new container instances"""
        if USE_MOCKS:
            new_ids = []
            for _ in range(count):
                c = mock_orch.create_container(image_id, resources or {})
                new_ids.append(c["id"])
            return {"started": new_ids}
        url = f"{self.orchestrator_url}/containers/{image_id}/start"
        data = {"count": count}
        if resources:
            data["resources"] = resources
        return await self._make_request(url, method="POST", json=data)

    async def stop_container(self, image_id: str, instance_id: str) -> Dict[str, Any]:
        """Stop a specific container instance"""
        if USE_MOCKS:
            ok = mock_orch.stop_container(instance_id)
            return {"stopped": ok}
        url = f"{self.orchestrator_url}/containers/{image_id}/stop"
        return await self._make_request(url, method="POST", json={"instanceId": instance_id})

    async def get_container_health(self, image_id: str) -> Dict[str, Any]:
        """Get health metrics for containers"""
        if USE_MOCKS:
            containers = mock_orch.get_containers_by_image(image_id)
            return {"errors": [], "containers": [mock_orch.get_container_health(c["id"]) for c in containers]}
        url = f"{self.orchestrator_url}/containers/{image_id}/health"
        return await self._make_request(url)

    async def update_container_resources(self, image_id: str, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Update resource limits for containers"""
        if USE_MOCKS:
            updated = []
            for c in mock_orch.get_containers_by_image(image_id):
                if mock_orch.update_container_resources(c["id"], resources):
                    updated.append(c["id"])
            return {"updated": updated}
        url = f"{self.orchestrator_url}/containers/{image_id}/resources"
        return await self._make_request(url, method="PUT", json=resources)

    # Load Balancer API calls
    async def get_traffic_stats(self, image_id: str) -> Dict[str, Any]:
        """Get traffic statistics for an image"""
        if USE_MOCKS:
            return mock_lb.get_traffic_stats(image_id)
        url = f"{self.load_balancer_url}/traffic/{image_id}"
        return await self._make_request(url)

    async def get_geographic_stats(self) -> Dict[str, Any]:
        """Get geographic distribution statistics"""
        url = f"{self.load_balancer_url}/geographic-stats"
        return await self._make_request(url)

    # Service Discovery API calls
    async def get_services(self) -> List[Dict[str, Any]]:
        """Get all registered services"""
        if USE_MOCKS:
            return [{"id": k, "name": k, **v} for k, v in mock_sd.get_system_services().items()]
        url = f"{self.service_discovery_url}/services"
        return await self._make_request(url)

    async def get_service_health(self, service_id: str) -> Dict[str, Any]:
        """Get health status of a specific service"""
        if USE_MOCKS:
            data = mock_sd.get_system_services().get(service_id, {"status": "unknown"})
            return {"status": data.get("status", "unknown"), "response_time": 50, "uptime": "99.9%"}
        url = f"{self.service_discovery_url}/health/{service_id}"
        return await self._make_request(url)

    # Billing API calls
    async def get_image_costs(self, image_id: str) -> Dict[str, Any]:
        """Get cost breakdown for an image"""
        if USE_MOCKS:
            # For mock, assume user_id unknown here
            return mock_billing.get_image_billing(image_id, "unknown-user")
        url = f"{self.billing_url}/images/{image_id}/costs"
        return await self._make_request(url)

    async def get_user_billing_summary(self, user_id: str) -> Dict[str, Any]:
        """Get billing summary for a user"""
        if USE_MOCKS:
            return mock_billing.get_user_billing_summary(user_id)
        url = f"{self.billing_url}/users/{user_id}/summary"
        return await self._make_request(url)

    async def get_payment_limit_status(self, image_id: str) -> Dict[str, Any]:
        """Get payment limit status for an image"""
        if USE_MOCKS:
            return mock_billing.check_payment_limit(image_id)
        url = f"{self.billing_url}/payment-limits/{image_id}"
        return await self._make_request(url)

    async def set_payment_limit(self, image_id: str, limit: float) -> Dict[str, Any]:
        """Set payment limit for an image"""
        if USE_MOCKS:
            ok = mock_billing.set_payment_limit(image_id, limit)
            return {"success": ok}
        url = f"{self.billing_url}/payment-limits/{image_id}"
        return await self._make_request(url, method="PUT", json={"limit": limit})

    async def get_billing_alerts(self) -> List[Dict[str, Any]]:
        """Get billing alerts"""
        url = f"{self.billing_url}/alerts"
        return await self._make_request(url)

    # Business Intelligence API calls
    async def get_revenue_analytics(self) -> Dict[str, Any]:
        """Get revenue analytics"""
        if USE_MOCKS:
            return mock_billing.get_system_bi_data()
        url = f"{self.billing_url}/bi/revenue"
        return await self._make_request(url)

    async def get_usage_analytics(self) -> Dict[str, Any]:
        """Get usage analytics"""
        if USE_MOCKS:
            return mock_billing.get_system_bi_data()
        url = f"{self.billing_url}/bi/usage"
        return await self._make_request(url)

# Global instance
external_client = ExternalServiceClient()

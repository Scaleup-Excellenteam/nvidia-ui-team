import httpx
import os
from typing import List, Optional, Dict, Any
from fastapi import HTTPException

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
    async def get_container_instances(self, image_id: str) -> List[Dict[str, Any]]:
        """Get all container instances for an image"""
        url = f"{self.orchestrator_url}/containers/{image_id}/instances"
        return await self._make_request(url)

    async def start_container(self, image_id: str, count: int = 1, resources: Optional[Dict] = None) -> Dict[str, Any]:
        """Start new container instances"""
        url = f"{self.orchestrator_url}/containers/{image_id}/start"
        data = {"count": count}
        if resources:
            data["resources"] = resources
        return await self._make_request(url, method="POST", json=data)

    async def stop_container(self, image_id: str, instance_id: str) -> Dict[str, Any]:
        """Stop a specific container instance"""
        url = f"{self.orchestrator_url}/containers/{image_id}/stop"
        return await self._make_request(url, method="POST", json={"instanceId": instance_id})

    async def get_container_health(self, image_id: str) -> Dict[str, Any]:
        """Get health metrics for containers"""
        url = f"{self.orchestrator_url}/containers/{image_id}/health"
        return await self._make_request(url)

    async def update_container_resources(self, image_id: str, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Update resource limits for containers"""
        url = f"{self.orchestrator_url}/containers/{image_id}/resources"
        return await self._make_request(url, method="PUT", json=resources)

    # Load Balancer API calls
    async def get_traffic_stats(self, image_id: str) -> Dict[str, Any]:
        """Get traffic statistics for an image"""
        url = f"{self.load_balancer_url}/traffic/{image_id}"
        return await self._make_request(url)

    async def get_geographic_stats(self) -> Dict[str, Any]:
        """Get geographic distribution statistics"""
        url = f"{self.load_balancer_url}/geographic-stats"
        return await self._make_request(url)

    # Service Discovery API calls
    async def get_services(self) -> List[Dict[str, Any]]:
        """Get all registered services"""
        url = f"{self.service_discovery_url}/services"
        return await self._make_request(url)

    async def get_service_health(self, service_id: str) -> Dict[str, Any]:
        """Get health status of a specific service"""
        url = f"{self.service_discovery_url}/health/{service_id}"
        return await self._make_request(url)

    # Billing API calls
    async def get_image_costs(self, image_id: str) -> Dict[str, Any]:
        """Get cost breakdown for an image"""
        url = f"{self.billing_url}/images/{image_id}/costs"
        return await self._make_request(url)

    async def get_user_billing_summary(self, user_id: str) -> Dict[str, Any]:
        """Get billing summary for a user"""
        url = f"{self.billing_url}/users/{user_id}/summary"
        return await self._make_request(url)

    async def get_payment_limit_status(self, image_id: str) -> Dict[str, Any]:
        """Get payment limit status for an image"""
        url = f"{self.billing_url}/payment-limits/{image_id}"
        return await self._make_request(url)

    async def set_payment_limit(self, image_id: str, limit: float) -> Dict[str, Any]:
        """Set payment limit for an image"""
        url = f"{self.billing_url}/payment-limits/{image_id}"
        return await self._make_request(url, method="PUT", json={"limit": limit})

    async def get_billing_alerts(self) -> List[Dict[str, Any]]:
        """Get billing alerts"""
        url = f"{self.billing_url}/alerts"
        return await self._make_request(url)

    # Business Intelligence API calls
    async def get_revenue_analytics(self) -> Dict[str, Any]:
        """Get revenue analytics"""
        url = f"{self.billing_url}/bi/revenue"
        return await self._make_request(url)

    async def get_usage_analytics(self) -> Dict[str, Any]:
        """Get usage analytics"""
        url = f"{self.billing_url}/bi/usage"
        return await self._make_request(url)

# Global instance
external_client = ExternalServiceClient()

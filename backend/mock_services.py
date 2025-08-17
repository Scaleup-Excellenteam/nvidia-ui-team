"""
Mock Services for Teams 2, 3, and 4
This module provides mock implementations of all external team services
that the UI team needs to interact with.
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid

class MockLoadBalancer:
    """Mock for Team 2 - Load Balancer"""
    
    def __init__(self):
        self.traffic_data = {}
        self.request_counts = {}
        self.geographic_routing = {}
        
    def get_traffic_stats(self, image_id: str) -> Dict[str, Any]:
        """Get traffic statistics for an image (RPS, geographic distribution)"""
        if image_id not in self.traffic_data:
            self.traffic_data[image_id] = {
                "requests_per_second": random.uniform(10, 100),
                "total_requests": random.randint(1000, 50000),
                "geographic_distribution": {
                    "US": random.randint(30, 60),
                    "EU": random.randint(20, 40),
                    "Asia": random.randint(10, 30)
                },
                "last_updated": datetime.now().isoformat()
            }
        
        return self.traffic_data[image_id]
    
    def get_all_traffic_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get traffic stats for all images"""
        return self.traffic_data
    
    def update_traffic_data(self, image_id: str, requests: int):
        """Update traffic data for an image"""
        if image_id not in self.traffic_data:
            self.traffic_data[image_id] = {
                "requests_per_second": 0,
                "total_requests": 0,
                "geographic_distribution": {"US": 0, "EU": 0, "Asia": 0},
                "last_updated": datetime.now().isoformat()
            }
        
        self.traffic_data[image_id]["total_requests"] += requests
        self.traffic_data[image_id]["requests_per_second"] = random.uniform(10, 100)
        self.traffic_data[image_id]["last_updated"] = datetime.now().isoformat()

class MockServiceDiscovery:
    """Mock for Team 2 - Service Discovery"""
    
    def __init__(self):
        self.system_services = {
            "load_balancer": {"status": "healthy", "endpoint": "http://localhost:8001"},
            "orchestrator": {"status": "healthy", "endpoint": "http://localhost:8002"},
            "billing": {"status": "healthy", "endpoint": "http://localhost:8003"},
            "discovery": {"status": "healthy", "endpoint": "http://localhost:8004"}
        }
        self.customer_containers = {}
        
    def get_system_services(self) -> Dict[str, Dict[str, str]]:
        """Get all system services registry"""
        return self.system_services
    
    def get_customer_containers(self, image_id: str = None) -> Dict[str, Dict[str, Any]]:
        """Get customer containers registry"""
        if image_id:
            return {k: v for k, v in self.customer_containers.items() if v.get("image_id") == image_id}
        return self.customer_containers
    
    def register_container(self, container_id: str, image_id: str, endpoint: str, status: str = "healthy"):
        """Register a new container"""
        self.customer_containers[container_id] = {
            "image_id": image_id,
            "endpoint": endpoint,
            "status": status,
            "registered_at": datetime.now().isoformat()
        }
    
    def update_container_status(self, container_id: str, status: str):
        """Update container status"""
        if container_id in self.customer_containers:
            self.customer_containers[container_id]["status"] = status
            self.customer_containers[container_id]["last_updated"] = datetime.now().isoformat()
    
    def unregister_container(self, container_id: str):
        """Unregister a container"""
        if container_id in self.customer_containers:
            del self.customer_containers[container_id]

class MockOrchestrator:
    """Mock for Team 3 - Orchestrator"""
    
    def __init__(self):
        self.containers = {}
        self.container_health = {}
        self.resource_limits = {}
        
        # Add some sample containers for testing
        self._add_sample_containers()
    
    def _add_sample_containers(self):
        """Add sample containers for testing"""
        sample_containers = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "image_id": "nginx:latest",
                "status": "running",
                "resources": {"cpu_limit": "1.0", "memory_limit": "512MB", "disk_limit": "10GB"},
                "health": {"cpu_usage": 45.2, "memory_usage": 67.8, "disk_usage": 23.1, "status": "healthy"},
                "created_at": datetime.now().isoformat(),
                "endpoint": "http://localhost:9001"
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440001", 
                "image_id": "nginx:latest",
                "status": "running",
                "resources": {"cpu_limit": "1.0", "memory_limit": "512MB", "disk_limit": "10GB"},
                "health": {"cpu_usage": 38.7, "memory_usage": 72.3, "disk_usage": 19.5, "status": "healthy"},
                "created_at": datetime.now().isoformat(),
                "endpoint": "http://localhost:9002"
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "image_id": "redis:latest", 
                "status": "stopped",
                "resources": {"cpu_limit": "0.5", "memory_limit": "256MB", "disk_limit": "5GB"},
                "health": {"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 12.8, "status": "stopped"},
                "created_at": datetime.now().isoformat(),
                "endpoint": "http://localhost:9003"
            }
        ]
        
        for container in sample_containers:
            self.containers[container["id"]] = container
            self.container_health[container["id"]] = container["health"]
            self.resource_limits[container["id"]] = container["resources"]
        
    def create_container(self, image_id: str, resources: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new container instance"""
        container_id = str(uuid.uuid4())
        
        default_resources = {
            "cpu_limit": "1.0",
            "memory_limit": "512MB",
            "disk_limit": "10GB"
        }
        
        if resources:
            default_resources.update(resources)
        
        container = {
            "id": container_id,
            "image_id": image_id,
            "status": "running",
            "resources": default_resources,
            "health": {
                "cpu_usage": random.uniform(10, 80),
                "memory_usage": random.uniform(20, 90),
                "disk_usage": random.uniform(5, 60),
                "status": "healthy"
            },
            "created_at": datetime.now().isoformat(),
            "endpoint": f"http://localhost:{random.randint(9000, 9999)}"
        }
        
        self.containers[container_id] = container
        self.container_health[container_id] = container["health"]
        self.resource_limits[container_id] = default_resources
        
        return container
    
    def start_container(self, container_id: str) -> bool:
        """Start a container"""
        if container_id in self.containers:
            self.containers[container_id]["status"] = "running"
            return True
        return False
    
    def stop_container(self, container_id: str) -> bool:
        """Stop a container"""
        if container_id in self.containers:
            self.containers[container_id]["status"] = "stopped"
            return True
        return False
    
    def delete_container(self, container_id: str) -> bool:
        """Delete a container"""
        if container_id in self.containers:
            del self.containers[container_id]
            if container_id in self.container_health:
                del self.container_health[container_id]
            if container_id in self.resource_limits:
                del self.resource_limits[container_id]
            return True
        return False
    
    def get_container_health(self, container_id: str) -> Dict[str, Any]:
        """Get container health metrics"""
        if container_id in self.container_health:
            # Simulate changing health metrics
            health = self.container_health[container_id]
            health["cpu_usage"] = max(0, min(100, health["cpu_usage"] + random.uniform(-5, 5)))
            health["memory_usage"] = max(0, min(100, health["memory_usage"] + random.uniform(-3, 3)))
            health["disk_usage"] = max(0, min(100, health["disk_usage"] + random.uniform(-1, 1)))
            
            # Determine overall health status
            if health["cpu_usage"] > 90 or health["memory_usage"] > 95:
                health["status"] = "critical"
            elif health["cpu_usage"] > 80 or health["memory_usage"] > 85:
                health["status"] = "warning"
            else:
                health["status"] = "healthy"
                
            return health
        return None
    
    def get_containers_by_image(self, image_id: str) -> List[Dict[str, Any]]:
        """Get all containers for a specific image"""
        return [container for container in self.containers.values() if container["image_id"] == image_id]
    
    def update_container_resources(self, container_id: str, resources: Dict[str, Any]) -> bool:
        """Update container resource limits"""
        if container_id in self.containers:
            self.containers[container_id]["resources"].update(resources)
            self.resource_limits[container_id].update(resources)
            return True
        return False
    
    def get_container_errors(self, container_id: str) -> List[str]:
        """Get container error logs"""
        if container_id in self.containers:
            # Simulate random errors
            errors = []
            if random.random() < 0.1:  # 10% chance of error
                error_types = [
                    "Connection timeout",
                    "Memory allocation failed",
                    "Disk space low",
                    "Process crashed",
                    "Network unreachable"
                ]
                errors.append(random.choice(error_types))
            return errors
        return []
    
    def scale_containers(self, image_id: str, target_count: int) -> List[str]:
        """Scale containers for an image"""
        current_containers = self.get_containers_by_image(image_id)
        current_count = len(current_containers)
        
        if target_count > current_count:
            # Scale up
            new_containers = []
            for _ in range(target_count - current_count):
                container = self.create_container(image_id)
                new_containers.append(container["id"])
            return new_containers
        elif target_count < current_count:
            # Scale down
            containers_to_remove = current_containers[:current_count - target_count]
            removed_ids = []
            for container in containers_to_remove:
                self.delete_container(container["id"])
                removed_ids.append(container["id"])
            return removed_ids
        
        return []

class MockBilling:
    """Mock for Team 4 - Billing"""
    
    def __init__(self):
        self.billing_data = {}
        self.pricing = {
            "cpu_per_hour": 0.05,  # $0.05 per CPU hour
            "memory_per_gb_hour": 0.02,  # $0.02 per GB hour
            "storage_per_gb_hour": 0.01,  # $0.01 per GB hour
            "requests_per_1000": 0.001  # $0.001 per 1000 requests
        }
        
    def calculate_container_cost(self, container_id: str, duration_hours: float, 
                               cpu_usage: float, memory_gb: float, storage_gb: float, 
                               requests: int) -> float:
        """Calculate cost for a container"""
        cpu_cost = (cpu_usage / 100) * self.pricing["cpu_per_hour"] * duration_hours
        memory_cost = memory_gb * self.pricing["memory_per_gb_hour"] * duration_hours
        storage_cost = storage_gb * self.pricing["storage_per_gb_hour"] * duration_hours
        request_cost = (requests / 1000) * self.pricing["requests_per_1000"]
        
        total_cost = cpu_cost + memory_cost + storage_cost + request_cost
        return round(total_cost, 4)
    
    def get_image_billing(self, image_id: str, user_id: str) -> Dict[str, Any]:
        """Get billing information for an image"""
        if image_id not in self.billing_data:
            # Generate mock billing data
            containers = random.randint(1, 5)
            total_hours = random.uniform(10, 720)  # 10 hours to 30 days
            total_requests = random.randint(1000, 100000)
            
            billing_info = {
                "image_id": image_id,
                "user_id": user_id,
                "total_cost": round(random.uniform(5, 500), 2),
                "containers_count": containers,
                "total_hours": total_hours,
                "total_requests": total_requests,
                "cost_breakdown": {
                    "cpu": round(random.uniform(1, 100), 2),
                    "memory": round(random.uniform(1, 50), 2),
                    "storage": round(random.uniform(1, 25), 2),
                    "requests": round(random.uniform(0.1, 10), 2)
                },
                "billing_period": "monthly",
                "last_updated": datetime.now().isoformat()
            }
            
            self.billing_data[image_id] = billing_info
        
        return self.billing_data[image_id]
    
    def get_user_billing_summary(self, user_id: str) -> Dict[str, Any]:
        """Get billing summary for a user"""
        user_images = [data for data in self.billing_data.values() if data["user_id"] == user_id]
        
        total_cost = sum(img["total_cost"] for img in user_images)
        total_containers = sum(img["containers_count"] for img in user_images)
        total_requests = sum(img["total_requests"] for img in user_images)
        
        return {
            "user_id": user_id,
            "total_cost": round(total_cost, 2),
            "total_containers": total_containers,
            "total_requests": total_requests,
            "images_count": len(user_images),
            "billing_period": "monthly",
            "last_updated": datetime.now().isoformat()
        }
    
    def get_system_bi_data(self) -> Dict[str, Any]:
        """Get system-wide BI data for admin dashboard"""
        total_revenue = sum(data["total_cost"] for data in self.billing_data.values())
        total_users = len(set(data["user_id"] for data in self.billing_data.values()))
        total_images = len(self.billing_data)
        total_containers = sum(data["containers_count"] for data in self.billing_data.values())
        
        # Generate historical data for charts
        historical_data = []
        for i in range(30):  # Last 30 days
            date = datetime.now() - timedelta(days=i)
            historical_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "revenue": round(random.uniform(50, 200), 2),
                "active_containers": random.randint(10, 50),
                "total_requests": random.randint(10000, 100000)
            })
        
        return {
            "total_revenue": round(total_revenue, 2),
            "total_users": total_users,
            "total_images": total_images,
            "total_containers": total_containers,
            "monthly_growth": round(random.uniform(5, 25), 1),  # Percentage
            "historical_data": historical_data,
            "top_performing_images": self._get_top_performing_images(),
            "revenue_forecast": self._get_revenue_forecast(),
            "last_updated": datetime.now().isoformat()
        }
    
    def _get_top_performing_images(self) -> List[Dict[str, Any]]:
        """Get top performing images by revenue"""
        sorted_images = sorted(self.billing_data.values(), 
                             key=lambda x: x["total_cost"], reverse=True)[:5]
        
        return [{
            "image_id": img["image_id"],
            "revenue": img["total_cost"],
            "containers": img["containers_count"],
            "requests": img["total_requests"]
        } for img in sorted_images]
    
    def _get_revenue_forecast(self) -> Dict[str, float]:
        """Get revenue forecast for next 3 months"""
        current_revenue = sum(data["total_cost"] for data in self.billing_data.values())
        
        return {
            "next_month": round(current_revenue * random.uniform(1.1, 1.3), 2),
            "next_2_months": round(current_revenue * random.uniform(1.2, 1.5), 2),
            "next_3_months": round(current_revenue * random.uniform(1.3, 1.8), 2)
        }
    
    def set_payment_limit(self, image_id: str, limit: float) -> bool:
        """Set payment limit for an image"""
        if image_id in self.billing_data:
            self.billing_data[image_id]["payment_limit"] = limit
            return True
        return False
    
    def check_payment_limit(self, image_id: str) -> Dict[str, Any]:
        """Check if image has reached payment limit"""
        if image_id in self.billing_data:
            current_cost = self.billing_data[image_id]["total_cost"]
            limit = self.billing_data[image_id].get("payment_limit", float('inf'))
            
            return {
                "image_id": image_id,
                "current_cost": current_cost,
                "limit": limit,
                "limit_reached": current_cost >= limit,
                "remaining": max(0, limit - current_cost)
            }
        return None

# Global instances
load_balancer = MockLoadBalancer()
service_discovery = MockServiceDiscovery()
orchestrator = MockOrchestrator()
billing = MockBilling()

# Initialize with some mock data
def initialize_mock_data():
    """Initialize mock data for testing"""
    # Generate billing data for sample images
    sample_images = ["nginx:latest", "nodejs:16", "python:3.9", "redis:6"]
    
    for i, image in enumerate(sample_images):
        # Generate billing data
        billing.get_image_billing(image, f"user_{i % 3 + 1}")
        
        # Generate traffic data
        load_balancer.update_traffic_data(image, random.randint(1000, 10000))
    
    # Register our sample containers in service discovery
    for container_id, container in orchestrator.containers.items():
        service_discovery.register_container(
            container_id,
            container["image_id"],
            container["endpoint"],
            container["status"]
        )

# Initialize mock data when module is imported
initialize_mock_data()

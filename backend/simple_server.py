#!/usr/bin/env python3
"""
Simple HTTP Server for ScaleUp-Nvidia UI Backend
Provides all necessary endpoints for the UI team with mock integrations
"""

import json
import sqlite3
import jwt
import hashlib
import os
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

# Import mock services
from mock_services import (
    load_balancer, service_discovery, orchestrator, billing
)

# Configuration
SECRET_KEY = "your-secret-key-here"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Database setup
DB_PATH = "scaleup_nvidia.db"

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Docker images table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS docker_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            image_name TEXT NOT NULL,
            image_tag TEXT DEFAULT 'latest',
            internal_port INTEGER,
            min_containers INTEGER DEFAULT 1,
            max_containers INTEGER DEFAULT 5,
            cpu_limit TEXT DEFAULT '1.0',
            memory_limit TEXT DEFAULT '512MB',
            disk_limit TEXT DEFAULT '10GB',
            payment_limit REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create admin user if not exists
    admin_password_hash = hashlib.sha256("Admin".encode()).hexdigest()
    cursor.execute('''
        INSERT OR IGNORE INTO users (email, password_hash, is_admin)
        VALUES (?, ?, ?)
    ''', ("Admin@gmail.com", admin_password_hash, True))
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash

def create_jwt_token(user_id, email, is_admin=False):
    """Create JWT token"""
    payload = {
        "user_id": user_id,
        "email": email,
        "is_admin": is_admin,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_from_token(auth_header):
    """Get user from Authorization header"""
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    return verify_jwt_token(token)

class ScaleUpNvidiaHandler(BaseHTTPRequestHandler):
    """HTTP request handler for ScaleUp-Nvidia API"""
    
    def _set_headers(self, status_code=200, content_type="application/json"):
        """Set response headers"""
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
    
    def _send_json_response(self, data, status_code=200):
        """Send JSON response"""
        self._set_headers(status_code)
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def _send_html_response(self, html_content, status_code=200):
        """Send HTML response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def _send_error(self, message, status_code=400):
        """Send error response"""
        self._send_json_response({"error": message}, status_code)
    
    def _get_request_body(self):
        """Get request body as JSON"""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            body = self.rfile.read(content_length)
            return json.loads(body.decode())
        return {}
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        try:
            if path == "/":
                # Root endpoint - serve HTML dashboard
                self._send_html_response(self._get_dashboard_html())
            
            elif path == "/auth/me":
                # Get current user info
                user = get_user_from_token(self.headers.get("Authorization"))
                if not user:
                    return self._send_error("Unauthorized", 401)
                
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT id, email, is_admin FROM users WHERE id = ?", (user["user_id"],))
                user_data = cursor.fetchone()
                conn.close()
                
                if user_data:
                    self._send_json_response({
                        "id": user_data[0],
                        "email": user_data[1],
                        "is_admin": bool(user_data[2])
                    })
                else:
                    self._send_error("User not found", 404)
            
            elif path == "/docker/images":
                # Get Docker images
                user = get_user_from_token(self.headers.get("Authorization"))
                if not user:
                    return self._send_error("Unauthorized", 401)
                
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                if user.get("is_admin"):
                    # Admin can see all images
                    cursor.execute("""
                        SELECT di.*, u.email as user_email 
                        FROM docker_images di 
                        JOIN users u ON di.user_id = u.id
                    """)
                else:
                    # Regular user sees only their images
                    cursor.execute("""
                        SELECT di.*, u.email as user_email 
                        FROM docker_images di 
                        JOIN users u ON di.user_id = u.id 
                        WHERE di.user_id = ?
                    """, (user["user_id"],))
                
                images = []
                for row in cursor.fetchall():
                    image_data = {
                        "id": row[0],
                        "user_id": row[1],
                        "image_name": row[2],
                        "image_tag": row[3],
                        "internal_port": row[4],
                        "min_containers": row[5],
                        "max_containers": row[6],
                        "cpu_limit": row[7],
                        "memory_limit": row[8],
                        "disk_limit": row[9],
                        "payment_limit": row[10],
                        "created_at": row[11],
                        "user_email": row[12]
                    }
                    
                    # Get additional data from mock services
                    image_id = f"{row[2]}:{row[3]}"
                    
                    # Get container count from orchestrator
                    containers = orchestrator.get_containers_by_image(image_id)
                    image_data["running_containers"] = len([c for c in containers if c["status"] == "running"])
                    image_data["total_containers"] = len(containers)
                    
                    # Get traffic stats from load balancer
                    traffic_stats = load_balancer.get_traffic_stats(image_id)
                    image_data["requests_per_second"] = traffic_stats["requests_per_second"]
                    image_data["total_requests"] = traffic_stats["total_requests"]
                    
                    # Get billing info
                    billing_info = billing.get_image_billing(image_id, str(row[1]))
                    image_data["total_cost"] = billing_info["total_cost"]
                    image_data["cost_breakdown"] = billing_info["cost_breakdown"]
                    
                    # Get container health summary
                    healthy_containers = 0
                    total_errors = 0
                    for container in containers:
                        health = orchestrator.get_container_health(container["id"])
                        if health and health["status"] == "healthy":
                            healthy_containers += 1
                        errors = orchestrator.get_container_errors(container["id"])
                        total_errors += len(errors)
                    
                    image_data["healthy_containers"] = healthy_containers
                    image_data["total_errors"] = total_errors
                    
                    images.append(image_data)
                
                conn.close()
                self._send_json_response({"images": images})
            
            elif path == "/containers":
                # Get containers for an image
                user = get_user_from_token(self.headers.get("Authorization"))
                if not user:
                    return self._send_error("Unauthorized", 401)
                
                image_id = query_params.get("image_id", [None])[0]
                if not image_id:
                    return self._send_error("image_id parameter required")
                
                containers = orchestrator.get_containers_by_image(image_id)
                
                # Add health data to each container
                for container in containers:
                    health = orchestrator.get_container_health(container["id"])
                    errors = orchestrator.get_container_errors(container["id"])
                    container["health"] = health
                    container["errors"] = errors
                
                self._send_json_response({"containers": containers})
            
            elif path == "/health":
                # System health check (admin only)
                user = get_user_from_token(self.headers.get("Authorization"))
                if not user or not user.get("is_admin"):
                    return self._send_error("Admin access required", 403)
                
                # Get system services status
                system_services = service_discovery.get_system_services()
                
                # Get system BI data
                bi_data = billing.get_system_bi_data()
                
                health_data = {
                    "system_services": system_services,
                    "bi_data": bi_data,
                    "timestamp": datetime.now().isoformat()
                }
                
                self._send_json_response(health_data)
            
            elif path == "/billing/summary":
                # Get billing summary for user
                user = get_user_from_token(self.headers.get("Authorization"))
                if not user:
                    return self._send_error("Unauthorized", 401)
                
                billing_summary = billing.get_user_billing_summary(str(user["user_id"]))
                self._send_json_response(billing_summary)
             
            elif path == "/billing/image":
                # Get billing for specific image
                user = get_user_from_token(self.headers.get("Authorization"))
                if not user:
                    return self._send_error("Unauthorized", 401)
                 
                image_id = query_params.get("image_id", [None])[0]
                if not image_id:
                    return self._send_error("image_id parameter required")
                 
                billing_info = billing.get_image_billing(image_id, str(user["user_id"]))
                self._send_json_response(billing_info)
             
            elif path == "/debug/containers":
                # Debug endpoint to see all containers
                user = get_user_from_token(self.headers.get("Authorization"))
                if not user:
                    return self._send_error("Unauthorized", 401)
                 
                all_containers = list(orchestrator.containers.keys())
                container_details = {}
                for container_id in all_containers:
                    container = orchestrator.containers[container_id]
                    container_details[container_id] = {
                        "image_id": container["image_id"],
                        "status": container["status"],
                        "endpoint": container["endpoint"]
                    }
                 
                self._send_json_response({
                    "total_containers": len(all_containers),
                    "container_ids": all_containers,
                    "container_details": container_details
                })
             
            else:
                self._send_error("Endpoint not found", 404)
                
        except Exception as e:
            self._send_error(f"Internal server error: {str(e)}", 500)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        try:
            if path == "/auth/signup":
                # User registration
                data = self._get_request_body()
                email = data.get("email")
                password = data.get("password")
                
                if not email or not password:
                    return self._send_error("Email and password required")
                
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Check if user already exists
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    conn.close()
                    return self._send_error("User already exists", 409)
                
                # Create new user
                password_hash = hash_password(password)
                cursor.execute(
                    "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                    (email, password_hash)
                )
                user_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                # Create JWT token
                token = create_jwt_token(user_id, email)
                
                self._send_json_response({
                    "message": "User created successfully",
                    "token": token,
                    "user": {"id": user_id, "email": email, "is_admin": False}
                })
            
            elif path == "/auth/signin":
                # User login
                data = self._get_request_body()
                email = data.get("email")
                password = data.get("password")
                
                if not email or not password:
                    return self._send_error("Email and password required")
                
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT id, password_hash, is_admin FROM users WHERE email = ?", (email,))
                user_data = cursor.fetchone()
                conn.close()
                
                if not user_data or not verify_password(password, user_data[1]):
                    return self._send_error("Invalid credentials", 401)
                
                # Create JWT token
                token = create_jwt_token(user_data[0], email, user_data[2])
                
                self._send_json_response({
                    "message": "Login successful",
                    "token": token,
                    "user": {
                        "id": user_data[0],
                        "email": email,
                        "is_admin": bool(user_data[2])
                    }
                })
            
            elif path == "/docker/images":
                # Create new Docker image
                user = get_user_from_token(self.headers.get("Authorization"))
                if not user:
                    return self._send_error("Unauthorized", 401)
                
                data = self._get_request_body()
                image_name = data.get("image_name")
                image_tag = data.get("image_tag", "latest")
                internal_port = data.get("internal_port")
                min_containers = data.get("min_containers", 1)
                max_containers = data.get("max_containers", 5)
                cpu_limit = data.get("cpu_limit", "1.0")
                memory_limit = data.get("memory_limit", "512MB")
                disk_limit = data.get("disk_limit", "10GB")
                payment_limit = data.get("payment_limit")
                
                if not image_name:
                    return self._send_error("image_name required")
                
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO docker_images 
                    (user_id, image_name, image_tag, internal_port, min_containers, 
                     max_containers, cpu_limit, memory_limit, disk_limit, payment_limit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user["user_id"], image_name, image_tag, internal_port, min_containers,
                     max_containers, cpu_limit, memory_limit, disk_limit, payment_limit))
                
                image_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                self._send_json_response({
                    "message": "Docker image created successfully",
                    "image_id": image_id
                })
            
            elif path == "/containers/start":
                # Start containers for an image
                user = get_user_from_token(self.headers.get("Authorization"))
                if not user:
                    return self._send_error("Unauthorized", 401)
                
                data = self._get_request_body()
                image_id = data.get("image_id")
                count = data.get("count", 1)
                
                if not image_id:
                    return self._send_error("image_id required")
                
                # Create containers
                new_containers = []
                for _ in range(count):
                    container = orchestrator.create_container(image_id)
                    service_discovery.register_container(
                        container["id"], 
                        image_id, 
                        container["endpoint"]
                    )
                    new_containers.append(container["id"])
                
                self._send_json_response({
                    "message": f"Started {count} container(s)",
                    "container_ids": new_containers
                })
            
            elif path == "/containers/stop":
                # Stop containers for an image
                user = get_user_from_token(self.headers.get("Authorization"))
                if not user:
                    return self._send_error("Unauthorized", 401)
                
                data = self._get_request_body()
                container_id = data.get("container_id")
                
                if not container_id:
                    return self._send_error("container_id required")
                
                success = orchestrator.stop_container(container_id)
                if success:
                    service_discovery.update_container_status(container_id, "stopped")
                    self._send_json_response({"message": "Container stopped successfully"})
                else:
                    self._send_error("Container not found", 404)
            
            elif path == "/containers/delete":
                # Delete containers
                user = get_user_from_token(self.headers.get("Authorization"))
                if not user:
                    return self._send_error("Unauthorized", 401)
                
                data = self._get_request_body()
                container_id = data.get("container_id")
                
                if not container_id:
                    return self._send_error("container_id required")
                
                success = orchestrator.delete_container(container_id)
                if success:
                    service_discovery.unregister_container(container_id)
                    self._send_json_response({"message": "Container deleted successfully"})
                else:
                    self._send_error("Container not found", 404)
            
            elif path == "/containers/scale":
                # Scale containers for an image
                user = get_user_from_token(self.headers.get("Authorization"))
                if not user:
                    return self._send_error("Unauthorized", 401)
                
                data = self._get_request_body()
                image_id = data.get("image_id")
                target_count = data.get("target_count")
                
                if not image_id or target_count is None:
                    return self._send_error("image_id and target_count required")
                
                # Scale containers
                affected_containers = orchestrator.scale_containers(image_id, target_count)
                
                self._send_json_response({
                    "message": f"Scaled to {target_count} containers",
                    "affected_containers": affected_containers
                })
            
            else:
                self._send_error("Endpoint not found", 404)
                
        except Exception as e:
            self._send_error(f"Internal server error: {str(e)}", 500)
    
    def do_PUT(self):
        """Handle PUT requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        try:
            if path == "/docker/images":
                # Update Docker image settings
                user = get_user_from_token(self.headers.get("Authorization"))
                if not user:
                    return self._send_error("Unauthorized", 401)
                
                data = self._get_request_body()
                image_id = data.get("id")
                
                if not image_id:
                    return self._send_error("image id required")
                
                # Update fields
                update_fields = {}
                for field in ["min_containers", "max_containers", "cpu_limit", 
                             "memory_limit", "disk_limit", "payment_limit"]:
                    if field in data:
                        update_fields[field] = data[field]
                
                if not update_fields:
                    return self._send_error("No fields to update")
                
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Build update query
                set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
                query = f"UPDATE docker_images SET {set_clause} WHERE id = ? AND user_id = ?"
                
                values = list(update_fields.values()) + [image_id, user["user_id"]]
                cursor.execute(query, values)
                
                if cursor.rowcount == 0:
                    conn.close()
                    return self._send_error("Image not found or access denied", 404)
                
                conn.commit()
                conn.close()
                
                self._send_json_response({"message": "Image updated successfully"})
            
            else:
                self._send_error("Endpoint not found", 404)
                
        except Exception as e:
            self._send_error(f"Internal server error: {str(e)}", 500)
    
    def _get_dashboard_html(self):
        """Generate HTML dashboard for API testing"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScaleUp-Nvidia Backend API Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .content {
            padding: 30px;
        }
        .section {
            margin-bottom: 30px;
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }
        .section h2 {
            margin: 0 0 20px 0;
            color: #2c3e50;
            font-size: 1.5em;
        }
        .endpoint-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .endpoint-card {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .endpoint-card h3 {
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 1.1em;
        }
        .method {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 10px;
        }
        .method.get { background: #d4edda; color: #155724; }
        .method.post { background: #d1ecf1; color: #0c5460; }
        .method.put { background: #fff3cd; color: #856404; }
        .method.delete { background: #f8d7da; color: #721c24; }
        .endpoint-path {
            font-family: monospace;
            background: #f8f9fa;
            padding: 5px 8px;
            border-radius: 4px;
            font-size: 0.9em;
            color: #495057;
        }
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            margin: 5px 5px 5px 0;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #5a6fd8;
        }
        .btn.secondary {
            background: #6c757d;
        }
        .btn.secondary:hover {
            background: #5a6268;
        }
        .btn.danger {
            background: #dc3545;
        }
        .btn.danger:hover {
            background: #c82333;
        }
        .response-area {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 15px;
            margin-top: 15px;
            font-family: monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
            display: none;
        }
        .auth-section {
            background: #e3f2fd;
            border-left-color: #2196f3;
        }
        .docker-section {
            background: #f3e5f5;
            border-left-color: #9c27b0;
        }
        .billing-section {
            background: #e8f5e8;
            border-left-color: #4caf50;
        }
        .system-section {
            background: #fff3e0;
            border-left-color: #ff9800;
        }
        .login-form {
            background: white;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #495057;
        }
        .form-group input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 1em;
        }
        .status {
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            font-weight: bold;
        }
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ScaleUp-Nvidia Backend API</h1>
            <p>Interactive API Testing Dashboard</p>
        </div>
        
        <div class="content">
            <!-- Authentication Section -->
            <div class="section auth-section">
                <h2>🔐 Authentication</h2>
                <div class="login-form">
                    <div class="form-group">
                        <label for="email">Email:</label>
                        <input type="email" id="email" value="Admin@gmail.com">
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" value="Admin">
                    </div>
                    <button class="btn" onclick="login()">Login</button>
                    <button class="btn secondary" onclick="signup()">Sign Up</button>
                    <button class="btn secondary" onclick="getCurrentUser()">Get Current User</button>
                </div>
                <div id="auth-status"></div>
            </div>

            <!-- Docker Images Section -->
            <div class="section docker-section">
                <h2>🐳 Docker Images</h2>
                <div class="endpoint-grid">
                    <div class="endpoint-card">
                        <h3><span class="method get">GET</span> List Images</h3>
                        <div class="endpoint-path">/docker/images</div>
                        <button class="btn" onclick="testEndpoint('GET', '/docker/images')">Test</button>
                    </div>
                    <div class="endpoint-card">
                        <h3><span class="method post">POST</span> Create Image</h3>
                        <div class="endpoint-path">/docker/images</div>
                        <button class="btn" onclick="createImage()">Test</button>
                    </div>
                </div>
            </div>

            <!-- Containers Section -->
            <div class="section docker-section">
                <h2>📦 Containers</h2>
                <div class="endpoint-grid">
                                         <div class="endpoint-card">
                         <h3><span class="method get">GET</span> Get Containers by Image</h3>
                         <div class="endpoint-path">/containers?image_id=nginx:latest</div>
                         <button class="btn" onclick="testEndpoint('GET', '/containers?image_id=nginx:latest')">Test</button>
                     </div>
                     <div class="endpoint-card">
                         <h3><span class="method get">GET</span> Debug All Containers</h3>
                         <div class="endpoint-path">/debug/containers</div>
                         <button class="btn secondary" onclick="testEndpoint('GET', '/debug/containers')">Debug</button>
                     </div>
                    <div class="endpoint-card">
                        <h3><span class="method post">POST</span> Start Containers</h3>
                        <div class="endpoint-path">/containers/start</div>
                        <button class="btn" onclick="testEndpoint('POST', '/containers/start', {image_id: 'nginx:latest', count: 2})">Test</button>
                    </div>
                                         <div class="endpoint-card">
                         <h3><span class="method post">POST</span> Stop Containers</h3>
                         <div class="endpoint-path">/containers/stop</div>
                         <button class="btn" onclick="testEndpoint('POST', '/containers/stop', {container_id: '550e8400-e29b-41d4-a716-446655440000'})">Test</button>
                     </div>
                                         <div class="endpoint-card">
                         <h3><span class="method post">POST</span> Scale Containers</h3>
                         <div class="endpoint-path">/containers/scale</div>
                         <button class="btn" onclick="testEndpoint('POST', '/containers/scale', {image_id: 'nginx:latest', target_count: 3})">Test</button>
                     </div>
                     <div class="endpoint-card">
                         <h3><span class="method post">POST</span> Delete Container</h3>
                         <div class="endpoint-path">/containers/delete</div>
                         <button class="btn danger" onclick="testEndpoint('POST', '/containers/delete', {container_id: '550e8400-e29b-41d4-a716-446655440000'})">Test</button>
                     </div>
                </div>
            </div>

            <!-- Billing Section -->
            <div class="section billing-section">
                <h2>💰 Billing</h2>
                <div class="endpoint-grid">
                    <div class="endpoint-card">
                        <h3><span class="method get">GET</span> Billing Summary</h3>
                        <div class="endpoint-path">/billing/summary</div>
                        <button class="btn" onclick="testEndpoint('GET', '/billing/summary')">Test</button>
                    </div>
                    <div class="endpoint-card">
                        <h3><span class="method get">GET</span> Image Billing</h3>
                        <div class="endpoint-path">/billing/image?image_id=test</div>
                        <button class="btn" onclick="testEndpoint('GET', '/billing/image?image_id=nginx:latest')">Test</button>
                    </div>
                </div>
            </div>

            <!-- System Section -->
            <div class="section system-section">
                <h2>⚙️ System</h2>
                <div class="endpoint-grid">
                    <div class="endpoint-card">
                        <h3><span class="method get">GET</span> Health Dashboard</h3>
                        <div class="endpoint-path">/health (Admin Only)</div>
                        <button class="btn" onclick="testEndpoint('GET', '/health')">Test</button>
                    </div>
                </div>
            </div>

            <!-- Response Area -->
            <div class="section">
                <h2>📋 Response</h2>
                <div id="response-area" class="response-area"></div>
            </div>
        </div>
    </div>

    <script>
        let authToken = '';

        function showStatus(message, type = 'info') {
            const statusDiv = document.getElementById('auth-status');
            statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
        }

        function showResponse(data) {
            const responseArea = document.getElementById('response-area');
            responseArea.style.display = 'block';
            responseArea.textContent = typeof data === 'object' ? JSON.stringify(data, null, 2) : data;
        }

        async function makeRequest(method, url, body = null) {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            if (authToken) {
                options.headers['Authorization'] = `Bearer ${authToken}`;
            }

            if (body) {
                options.body = JSON.stringify(body);
            }

            try {
                const response = await fetch(url, options);
                const data = await response.text();
                
                let parsedData;
                try {
                    parsedData = JSON.parse(data);
                } catch {
                    parsedData = data;
                }

                if (response.ok) {
                    showResponse(parsedData);
                } else {
                    showResponse({ error: parsedData, status: response.status });
                }
            } catch (error) {
                showResponse({ error: error.message });
            }
        }

        async function login() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('/auth/signin', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();
                
                if (response.ok) {
                    authToken = data.token;
                    showStatus('Login successful! Token saved.', 'success');
                    showResponse(data);
                } else {
                    showStatus('Login failed: ' + (data.error || 'Unknown error'), 'error');
                }
            } catch (error) {
                showStatus('Login error: ' + error.message, 'error');
            }
        }

        async function signup() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('/auth/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();
                
                if (response.ok) {
                    showStatus('Signup successful!', 'success');
                    showResponse(data);
                } else {
                    showStatus('Signup failed: ' + (data.error || 'Unknown error'), 'error');
                }
            } catch (error) {
                showStatus('Signup error: ' + error.message, 'error');
            }
        }

        async function getCurrentUser() {
            await makeRequest('GET', '/auth/me');
        }

        async function testEndpoint(method, path, body = null) {
            await makeRequest(method, path, body);
        }

        async function createImage() {
            const imageData = {
                image_name: 'nginx',
                image_tag: 'latest',
                internal_port: 80,
                min_containers: 1,
                max_containers: 5,
                cpu_limit: '1.0',
                memory_limit: '512MB',
                disk_limit: '10GB',
                payment_limit: 100.0
            };
            await makeRequest('POST', '/docker/images', imageData);
        }
    </script>
</body>
</html>
        """

def run_server(port=8000):
    """Run the HTTP server"""
    server_address = ("", port)
    httpd = HTTPServer(server_address, ScaleUpNvidiaHandler)
    print(f"🚀 ScaleUp-Nvidia Backend Server running on port {port}")
    print(f"📡 API available at: http://localhost:{port}")
    print(f"🔗 Frontend should connect to: http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.server_close()

if __name__ == "__main__":
    # Initialize database
    init_database()
    print("✅ Database initialized")
    
    # Run server
    run_server()

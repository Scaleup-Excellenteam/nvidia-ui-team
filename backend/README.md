# ScaleUp-Nvidia UI Backend

FastAPI backend for the ScaleUp-Nvidia container management platform UI team.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Setup

Copy `env.example` to `.env` and configure:

```bash
cp env.example .env
```

Update the `.env` file with your database and external service URLs.

### 3. Database Setup

Create a PostgreSQL database and update the `DATABASE_URL` in your `.env` file.

### 4. Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📋 API Endpoints

### Authentication

- `POST /auth/signup` - Register new user
- `POST /auth/signin` - User login
- `GET /auth/me` - Get current user info

### Docker Management

- `POST /docker/upload` - Upload Docker image
- `GET /docker/images` - Get all images
- `PUT /docker/images/{id}/restrictions` - Update image restrictions

### Health & Monitoring (Admin Only)

- `GET /health/system` - System health status
- `GET /health/bi` - Business intelligence metrics

## 🔗 External Service Integration

This backend integrates with other teams' services:

- **Orchestrator** (Team 3) - Container management
- **Load Balancer** (Team 2) - Traffic statistics
- **Service Discovery** (Team 2) - Service health
- **Billing** (Team 4) - Cost and payment data

## 🗄️ Database Schema

### Users Table

- `id` - Primary key
- `email` - Unique email address
- `first_name`, `last_name` - User names
- `hashed_password` - Encrypted password
- `is_admin` - Admin privileges
- `is_active` - Account status
- `created_at`, `updated_at` - Timestamps

### Docker Images Table

- `id` - Primary key
- `user_id` - Owner user ID
- `name` - Image name
- `image_file_path` - Stored file path
- `inner_port` - Container port
- `scaling_type` - Scaling strategy
- `min_containers`, `max_containers`, `static_containers` - Scaling limits
- `items_per_container` - Resource limits
- `payment_limit` - Payment threshold
- `description` - Optional description
- `status` - Current status
- `created_at`, `updated_at` - Timestamps

## 🔧 Development

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
alembic upgrade head
```

## 📝 Notes

- Admin user is automatically created when email is "admin@gmail.com"
- File uploads are stored in the `uploads/` directory
- External service calls are wrapped with error handling
- JWT tokens are used for authentication

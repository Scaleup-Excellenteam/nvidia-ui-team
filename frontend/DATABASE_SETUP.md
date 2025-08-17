# Database Setup Guide

## 🗄️ Database Configuration

Your upload functionality is now configured to post to a database! Here's how to set it up:

## 📋 Prerequisites

1. **Choose your database:**

   - PostgreSQL (recommended)
   - MySQL
   - MongoDB

2. **Install database driver:**

   ```bash
   # For PostgreSQL
   npm install pg @types/pg

   # For MySQL
   npm install mysql2 @types/mysql2

   # For MongoDB
   npm install mongoose
   ```

## 🔧 Environment Variables

Create a `.env.local` file in your `frontend` directory:

```env
# Database Configuration
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=docker_management
DB_USER=your_username
DB_PASSWORD=your_password

# File Storage
STORAGE_TYPE=local
UPLOAD_DIR=./uploads

# JWT Secret
JWT_SECRET=your-super-secret-jwt-key-here
```

## 🗃️ Database Setup

### PostgreSQL Setup

1. **Install PostgreSQL** (if not already installed)
2. **Create database:**
   ```sql
   CREATE DATABASE docker_management;
   ```
3. **Run the schema:**
   ```bash
   psql -d docker_management -f database-schema.sql
   ```

### MySQL Setup

1. **Install MySQL** (if not already installed)
2. **Create database:**
   ```sql
   CREATE DATABASE docker_management;
   ```
3. **Run the schema** (modify `database-schema.sql` for MySQL syntax)

## 🔄 Update API Routes

### 1. Update Upload Route

In `frontend/src/app/api/docker/upload/route.ts`, uncomment and configure your database connection:

```typescript
// For PostgreSQL
const { Pool } = require("pg");
return new Pool({
  user: process.env.DB_USER,
  host: process.env.DB_HOST,
  database: process.env.DB_NAME,
  password: process.env.DB_PASSWORD,
  port: process.env.DB_PORT,
});
```

### 2. Update Images Route

In `frontend/src/app/api/docker/images/route.ts`, uncomment and configure your database connection.

## 📁 File Storage Setup

### Local Storage

```bash
mkdir uploads
```

### AWS S3

Add to `.env.local`:

```env
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET=your-bucket-name
```

### Google Cloud Storage

Add to `.env.local`:

```env
STORAGE_TYPE=gcs
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
GCS_BUCKET=your-bucket-name
```

## 🚀 Testing

1. **Start your database server**
2. **Start the Next.js app:**
   ```bash
   npm run dev
   ```
3. **Sign in as admin:**
   - Email: `Admin@gmail.com`
   - Password: `Admin`
4. **Upload a Docker image** - it will now be saved to your database!

## 📊 Database Schema

The `docker_images` table includes:

- ✅ **Basic info:** name, file_path, inner_port
- ✅ **Scaling config:** scaling_type, min/max/static containers
- ✅ **Performance metrics:** instances, avg_requests_per_second, cost
- ✅ **Management:** item_restrictions, errors, payment, status
- ✅ **Timestamps:** created_at, updated_at

## 🔍 Monitoring

Check your database to see uploaded images:

```sql
SELECT * FROM docker_images ORDER BY created_at DESC;
```

## 🛠️ Customization

You can modify the database schema in `database-schema.sql` to add:

- User associations
- Additional metadata
- Performance tracking
- Cost calculations

Your upload system is now fully database-integrated! 🎉

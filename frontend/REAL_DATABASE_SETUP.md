# Real Database Connection Guide

## 🗄️ **Step 1: Install Database Driver**

Choose your database and install the appropriate driver:

```bash
# For PostgreSQL (Recommended)
npm install pg @types/pg

# For MySQL
npm install mysql2 @types/mysql2

# For MongoDB
npm install mongoose
```

## 🔧 **Step 2: Create Environment Variables**

Create a `.env.local` file in your `frontend` directory:

```env
# Database Configuration
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=docker_management
DB_USER=postgres
DB_PASSWORD=your_password_here

# File Storage
STORAGE_TYPE=local
UPLOAD_DIR=./uploads

# JWT Secret
JWT_SECRET=your-super-secret-jwt-key-here
```

## 🗃️ **Step 3: Database Setup**

### PostgreSQL Setup (Recommended)

1. **Install PostgreSQL:**

   ```bash
   # Windows (using chocolatey)
   choco install postgresql

   # Or download from https://www.postgresql.org/download/
   ```

2. **Create Database:**

   ```sql
   CREATE DATABASE docker_management;
   ```

3. **Run Schema:**
   ```bash
   psql -d docker_management -f database-schema.sql
   ```

### MySQL Setup

1. **Install MySQL:**

   ```bash
   # Windows (using chocolatey)
   choco install mysql
   ```

2. **Create Database:**

   ```sql
   CREATE DATABASE docker_management;
   ```

3. **Run Schema** (modify `database-schema.sql` for MySQL syntax)

## 🔄 **Step 4: Update API Routes**

### Update Upload Route (`frontend/src/app/api/docker/upload/route.ts`)

Replace the mock database connection with real connection:

```typescript
// For PostgreSQL
async function connectToDatabase() {
  const { Pool } = require("pg");
  return new Pool({
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    password: process.env.DB_PASSWORD,
    port: parseInt(process.env.DB_PORT || "5432"),
  });
}

// For MySQL
async function connectToDatabase() {
  const mysql = require("mysql2/promise");
  return mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
  });
}
```

### Update Images Route (`frontend/src/app/api/docker/images/route.ts`)

Apply the same database connection changes.

## 📁 **Step 5: File Storage Setup**

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

## 🚀 **Step 6: Test the Connection**

1. **Start your database server**
2. **Start the Next.js app:**
   ```bash
   npm run dev
   ```
3. **Sign in as admin:**
   - Email: `Admin@gmail.com`
   - Password: `Admin`
4. **Upload a Docker image** - it will now be saved to your real database!

## 🔍 **Step 7: Verify Database Connection**

Check your database to see uploaded images:

```sql
-- PostgreSQL
SELECT * FROM docker_images ORDER BY created_at DESC;

-- MySQL
SELECT * FROM docker_images ORDER BY created_at DESC;
```

## 🛠️ **Troubleshooting**

### Common Issues:

1. **Connection Refused:**

   - Ensure database server is running
   - Check host and port in `.env.local`
   - Verify firewall settings

2. **Authentication Failed:**

   - Check username and password
   - Ensure user has proper permissions

3. **Database Not Found:**

   - Create the database first
   - Run the schema file

4. **Permission Denied:**
   - Grant proper permissions to your database user
   - Check file permissions for uploads directory

## 📊 **Database Schema Overview**

The system uses these main tables:

- **`docker_images`**: Stores all uploaded Docker images and their configurations
- **`users`**: Stores user authentication data (optional)

Key fields in `docker_images`:

- `payment_limit`: Maximum payment allowed per image
- `scaling_type`: Container scaling strategy (minimal/maximal/static)
- `instances`: Current number of running containers
- `avg_requests_per_second`: Performance metrics
- `cost` and `payment`: Financial tracking

## 🔐 **Security Considerations**

1. **Environment Variables:** Never commit `.env.local` to version control
2. **Database Permissions:** Use least privilege principle
3. **File Uploads:** Validate file types and sizes
4. **Authentication:** Use strong passwords and JWT tokens

## 📈 **Monitoring**

Monitor your database performance:

```sql
-- Check table sizes
SELECT
  schemaname,
  tablename,
  attname,
  n_distinct,
  correlation
FROM pg_stats
WHERE tablename = 'docker_images';

-- Check recent uploads
SELECT
  name,
  created_at,
  status,
  payment_limit,
  payment
FROM docker_images
WHERE created_at > NOW() - INTERVAL '24 hours';
```

Your system is now ready for production use with real database integration! 🎉

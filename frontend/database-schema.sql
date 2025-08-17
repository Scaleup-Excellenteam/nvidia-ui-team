-- Database schema for Docker Images Management System

-- Create docker_images table
CREATE TABLE docker_images (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    inner_port INTEGER NOT NULL,
    scaling_type VARCHAR(50) NOT NULL CHECK (scaling_type IN ('minimal', 'maximal', 'static')),
    min_containers INTEGER DEFAULT 0,
    max_containers INTEGER DEFAULT 0,
    static_containers INTEGER DEFAULT 0,
    items_per_container INTEGER NOT NULL,
    payment_limit DECIMAL(10,2) DEFAULT 0.00,
    description TEXT,
    status VARCHAR(50) DEFAULT 'processing' CHECK (status IN ('processing', 'running', 'stopped', 'error')),
    instances INTEGER DEFAULT 0,
    avg_requests_per_second DECIMAL(10,2) DEFAULT 0.00,
    cost DECIMAL(10,2) DEFAULT 0.00,
    item_restrictions INTEGER DEFAULT 0,
    errors JSON DEFAULT '[]',
    payment DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for better performance
CREATE INDEX idx_docker_images_status ON docker_images(status);
CREATE INDEX idx_docker_images_created_at ON docker_images(created_at);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_docker_images_updated_at 
    BEFORE UPDATE ON docker_images 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Optional: Create users table for authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create trigger for users table
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample admin user (password: Admin)
INSERT INTO users (email, password_hash, first_name, last_name, is_admin) 
VALUES ('Admin@gmail.com', '$2b$10$hashedpasswordhere', 'Admin', 'User', true);

-- Sample data for testing
INSERT INTO docker_images (
    name, 
    file_path, 
    inner_port, 
    scaling_type, 
    min_containers, 
    max_containers, 
    static_containers, 
    items_per_container, 
    description, 
    status, 
    instances, 
    avg_requests_per_second, 
    cost, 
    item_restrictions, 
    errors, 
    payment
) VALUES 
('nginx-web-server', '/uploads/nginx-web-server_1234567890.tar', 80, 'static', 0, 0, 3, 1000, 'Nginx web server for static content', 'running', 3, 45.67, 12.50, 1000, '[]', 25.00),
('postgres-database', '/uploads/postgres-database_1234567891.tar', 5432, 'minimal', 2, 0, 0, 500, 'PostgreSQL database server', 'running', 2, 23.45, 8.75, 500, '["Connection timeout"]', 15.00),
('redis-cache', '/uploads/redis-cache_1234567892.tar', 6379, 'static', 0, 0, 1, 2000, 'Redis cache server', 'stopped', 1, 156.78, 5.25, 2000, '[]', 10.50),
('node-api-server', '/uploads/node-api-server_1234567893.tar', 3000, 'maximal', 0, 4, 0, 750, 'Node.js API server', 'error', 4, 89.12, 18.90, 750, '["Memory limit exceeded", "High CPU usage"]', 35.00);

import { NextRequest, NextResponse } from "next/server";

// Database connection function (same as in upload route)
async function connectToDatabase() {
  // Example for different databases:

  // For PostgreSQL with pg
  // const { Pool } = require('pg');
  // return new Pool({
  //   user: process.env.DB_USER,
  //   host: process.env.DB_HOST,
  //   database: process.env.DB_NAME,
  //   password: process.env.DB_PASSWORD,
  //   port: process.env.DB_PORT,
  // });

  // For MySQL with mysql2
  // const mysql = require('mysql2/promise');
  // return mysql.createConnection({
  //   host: process.env.DB_HOST,
  //   user: process.env.DB_USER,
  //   password: process.env.DB_PASSWORD,
  //   database: process.env.DB_NAME,
  // });

  // For MongoDB with mongoose
  // const mongoose = require('mongoose');
  // await mongoose.connect(process.env.MONGODB_URI);
  // return mongoose.connection;

  // For now, we'll use a mock database connection
  return {
    query: async (sql: string, params: any[]) => {
      console.log("Database query:", sql, params);
      // Return mock data for now
      return {
        rows: [
          {
            id: "1",
            name: "nginx-web-server",
            instances: 3,
            avg_requests_per_second: 45.67,
            cost: 12.5,
            item_restrictions: 1000,
            errors: [],
            payment: 25.0,
            status: "running",
          },
          {
            id: "2",
            name: "postgres-database",
            instances: 2,
            avg_requests_per_second: 23.45,
            cost: 8.75,
            item_restrictions: 500,
            errors: ["Connection timeout"],
            payment: 15.0,
            status: "running",
          },
          {
            id: "3",
            name: "redis-cache",
            instances: 1,
            avg_requests_per_second: 156.78,
            cost: 5.25,
            item_restrictions: 2000,
            errors: [],
            payment: 10.5,
            status: "stopped",
          },
          {
            id: "4",
            name: "node-api-server",
            instances: 4,
            avg_requests_per_second: 89.12,
            cost: 18.9,
            item_restrictions: 750,
            errors: ["Memory limit exceeded", "High CPU usage"],
            payment: 35.0,
            status: "error",
          },
        ],
      };
    },
  };
}

export async function GET(request: NextRequest) {
  try {
    // Get the authorization header
    const authHeader = request.headers.get("authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const token = authHeader.substring(7);

    // Only admin can see all images
    if (token !== "admin-token") {
      return NextResponse.json(
        { error: "Forbidden - Admin access required" },
        { status: 403 }
      );
    }

    // Connect to database
    const db = await connectToDatabase();

    // Fetch all docker images from database
    const selectQuery = `
      SELECT 
        id,
        name,
        instances,
        avg_requests_per_second,
        cost,
        item_restrictions,
        payment_limit,
        errors,
        payment,
        status,
        created_at,
        updated_at
      FROM docker_images 
      ORDER BY created_at DESC
    `;

    const result = await db.query(selectQuery, []);

    // Transform database results to match frontend expectations
    const images = result.rows.map((row: any) => ({
      id: row.id.toString(),
      name: row.name,
      instances: row.instances || 0,
      avgRequestsPerSecond: row.avg_requests_per_second || 0,
      cost: row.cost || 0,
      itemRestrictions: row.item_restrictions || 0,
      paymentLimit: row.payment_limit || 0,
      errors: row.errors ? JSON.parse(row.errors) : [],
      payment: row.payment || 0,
      status: row.status || "processing",
    }));

    return NextResponse.json({ images });
  } catch (error) {
    console.error("Error in /api/docker/images:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

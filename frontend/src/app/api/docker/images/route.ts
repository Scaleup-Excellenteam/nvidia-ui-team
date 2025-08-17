import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    // Get the authorization header
    const authHeader = request.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const token = authHeader.substring(7);

    // Check for hardcoded admin token first
    if (token === "admin-token") {
      // Return mock data for admin user
      const mockImages = [
        {
          id: "1",
          name: "nginx-web-server",
          instances: 3,
          avgRequestsPerSecond: 45.67,
          cost: 12.5,
          itemRestrictions: 1000,
          paymentLimit: 50.0,
          errors: [],
          payment: 25.0,
          status: "running",
        },
        {
          id: "2",
          name: "postgres-database",
          instances: 2,
          avgRequestsPerSecond: 23.45,
          cost: 8.75,
          itemRestrictions: 500,
          paymentLimit: 30.0,
          errors: ["Connection timeout"],
          payment: 15.0,
          status: "running",
        },
        {
          id: "3",
          name: "redis-cache",
          instances: 1,
          avgRequestsPerSecond: 156.78,
          cost: 5.25,
          itemRestrictions: 2000,
          paymentLimit: 25.0,
          errors: [],
          payment: 10.5,
          status: "stopped",
        },
        {
          id: "4",
          name: "node-api-server",
          instances: 4,
          avgRequestsPerSecond: 89.12,
          cost: 18.9,
          itemRestrictions: 750,
          paymentLimit: 75.0,
          errors: ["Memory limit exceeded", "High CPU usage"],
          payment: 35.0,
          status: "error",
        },
      ];

      return NextResponse.json({ images: mockImages });
    }

    // Try to call the FastAPI backend for other tokens
    try {
      const backendUrl = process.env.BACKEND_API_URL || "http://localhost:8000";
      const response = await fetch(`${backendUrl}/docker/images`, {
        method: "GET",
        headers: {
          Authorization: authHeader,
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(data, { status: response.status });
      }

      return NextResponse.json(data);
    } catch (backendError) {
      // If backend is not available, only allow admin token
      console.log("Backend not available, using fallback data");
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
  } catch (error) {
    console.error("Error in /api/docker/images:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    // Get the authorization header
    const authHeader = request.headers.get("authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      console.error(
        "GET /api/health/system - Unauthorized access attempt - missing or invalid authorization header"
      );
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const token = authHeader.substring(7);

    // Only admin can access health data
    if (token !== "admin-token") {
      console.error(
        "GET /api/health/system - Forbidden access attempt - admin access required"
      );
      return NextResponse.json(
        { error: "Forbidden - Admin access required" },
        { status: 403 }
      );
    }

    console.log("GET /api/health/system - System health requested by admin");

    // Mock system components data
    const systemComponents = [
      {
        name: "Load Balancer",
        status: "healthy" as const,
        uptime: "99.9%",
        responseTime: 45,
      },
      {
        name: "Database",
        status: "healthy" as const,
        uptime: "99.8%",
        responseTime: 12,
      },
      {
        name: "Container Orchestrator",
        status: "warning" as const,
        uptime: "98.5%",
        responseTime: 78,
      },
      {
        name: "Billing System",
        status: "healthy" as const,
        uptime: "99.7%",
        responseTime: 23,
      },
      {
        name: "File Storage",
        status: "healthy" as const,
        uptime: "99.9%",
        responseTime: 34,
      },
      {
        name: "Authentication Service",
        status: "healthy" as const,
        uptime: "99.6%",
        responseTime: 15,
      },
    ];

    console.log(
      "GET /api/health/system - System health data returned successfully"
    );
    return NextResponse.json({ components: systemComponents });
  } catch (error) {
    console.error(
      "GET /api/health/system - Error in /api/health/system:",
      error
    );
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

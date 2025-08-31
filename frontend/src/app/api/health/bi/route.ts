import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    // Get the authorization header
    const authHeader = request.headers.get("authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      console.error(
        "GET /api/health/bi - Unauthorized access attempt - missing or invalid authorization header"
      );
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const token = authHeader.substring(7);

    // Only admin can access BI data
    if (token !== "admin-token") {
      console.error(
        "GET /api/health/bi - Forbidden access attempt - admin access required"
      );
      return NextResponse.json(
        { error: "Forbidden - Admin access required" },
        { status: 403 }
      );
    }

    console.log("GET /api/health/bi - BI metrics requested by admin");

    // Mock BI metrics data
    const biMetrics = {
      totalRevenue: 1250.75,
      totalCustomers: 47,
      activeImages: 12,
      totalContainers: 28,
      averageLoad: 67.3,
    };

    console.log("GET /api/health/bi - BI metrics data returned successfully");
    return NextResponse.json(biMetrics);
  } catch (error) {
    console.error("GET /api/health/bi - Error in /api/health/bi:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

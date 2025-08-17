import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    // Get the authorization header
    const authHeader = request.headers.get("authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const token = authHeader.substring(7);

    // Only admin can access BI data
    if (token !== "admin-token") {
      return NextResponse.json(
        { error: "Forbidden - Admin access required" },
        { status: 403 }
      );
    }

    // Mock BI metrics data
    const biMetrics = {
      totalRevenue: 1250.75,
      totalCustomers: 47,
      activeImages: 12,
      totalContainers: 28,
      averageLoad: 67.3,
    };

    return NextResponse.json(biMetrics);
  } catch (error) {
    console.error("Error in /api/health/bi:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

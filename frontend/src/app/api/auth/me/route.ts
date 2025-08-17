import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const token = authHeader.substring(7);

    // Check for hardcoded admin token first
    if (token === "admin-token") {
      return NextResponse.json({
        email: "Admin@gmail.com",
        name: "Admin User",
      });
    }

    // Try to call the FastAPI backend for other tokens
    try {
      const backendUrl = process.env.BACKEND_API_URL || "http://localhost:8000";
      const response = await fetch(`${backendUrl}/auth/me`, {
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
      console.log("Backend not available, using fallback authentication");
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
  } catch (error) {
    console.error("Error in /api/auth/me:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

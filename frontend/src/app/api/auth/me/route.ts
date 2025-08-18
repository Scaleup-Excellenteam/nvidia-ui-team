import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      console.error(
        "GET /api/auth/me - Unauthorized access attempt - missing or invalid authorization header"
      );
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    console.log("GET /api/auth/me - User info requested");

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
      console.error(
        `GET /api/auth/me - Failed to get user info, status: ${response.status}`
      );
      return NextResponse.json(data, { status: response.status });
    }

    console.log("GET /api/auth/me - User info retrieved successfully");
    return NextResponse.json(data);
  } catch (error) {
    console.error("GET /api/auth/me - Error in /api/auth/me:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

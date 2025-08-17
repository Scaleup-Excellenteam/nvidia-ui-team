import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password } = body;

    // Check for hardcoded admin user first
    if (email === "Admin@gmail.com" && password === "Admin") {
      return NextResponse.json({
        success: true,
        token: "admin-token",
        user: { email: "Admin@gmail.com", name: "Admin User" },
      });
    }

    // Try to call the FastAPI backend for other users
    try {
      const backendUrl = process.env.BACKEND_API_URL || "http://localhost:8000";
      const response = await fetch(`${backendUrl}/auth/signin`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(data, { status: response.status });
      }

      return NextResponse.json(data);
    } catch (backendError) {
      // If backend is not available, only allow admin user
      console.log("Backend not available, using fallback authentication");
      return NextResponse.json(
        { error: "Invalid credentials" },
        { status: 401 }
      );
    }
  } catch (error) {
    console.error("Error in /api/auth/signin:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

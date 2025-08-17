import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password } = body;

    // Mock authentication logic
    if (email === "Admin@gmail.com" && password === "Admin") {
      return NextResponse.json({
        success: true,
        token: "admin-token",
        user: { email: "Admin@gmail.com", name: "Admin User" },
      });
    } else if (email === "user@example.com" && password === "password") {
      return NextResponse.json({
        success: true,
        token: "user-token",
        user: { email: "user@example.com", name: "Regular User" },
      });
    } else if (email === "test@example.com" && password === "test") {
      return NextResponse.json({
        success: true,
        token: "test-token",
        user: { email: "test@example.com", name: "Test User" },
      });
    } else {
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

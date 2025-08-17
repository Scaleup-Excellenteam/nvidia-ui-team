import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    // Get the authorization header
    const authHeader = request.headers.get("authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const token = authHeader.substring(7); // Remove 'Bearer ' prefix

    // For demo purposes, we'll simulate different users based on the token
    // In a real app, you'd validate the token with your backend

    // Mock user data - you can modify this for testing
    const mockUsers = {
      "admin-token": { email: "Admin@gmail.com", name: "Admin User" },
      "user-token": { email: "user@example.com", name: "Regular User" },
      "test-token": { email: "test@example.com", name: "Test User" },
    };

    const userData = mockUsers[token as keyof typeof mockUsers] || {
      email: "unknown@example.com",
      name: "Unknown User",
    };

    return NextResponse.json(userData);
  } catch (error) {
    console.error("Error in /api/auth/me:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

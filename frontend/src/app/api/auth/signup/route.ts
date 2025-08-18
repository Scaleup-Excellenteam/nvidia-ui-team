import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { firstName, lastName, email, password } = body;

    console.log(
      `POST /api/auth/signup - Registration attempt for email: ${email}`
    );

    // Call the FastAPI backend
    const backendUrl = process.env.BACKEND_API_URL || "http://localhost:8000";
    const response = await fetch(`${backendUrl}/auth/signup`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ firstName, lastName, email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(
        `POST /api/auth/signup - Registration failed for email: ${email}, status: ${response.status}`
      );
      return NextResponse.json(data, { status: response.status });
    }

    console.log(
      `POST /api/auth/signup - Registration successful for email: ${email}`
    );
    return NextResponse.json(data);
  } catch (error) {
    console.error("POST /api/auth/signup - Error in /api/auth/signup:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

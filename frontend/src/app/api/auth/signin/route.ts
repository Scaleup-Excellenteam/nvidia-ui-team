import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password } = body;

    console.log(`POST /api/auth/signin - Login attempt for email: ${email}`);

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
      console.error(
        `POST /api/auth/signin - Login failed for email: ${email}, status: ${response.status}`
      );
      return NextResponse.json(data, { status: response.status });
    }

    console.log(`POST /api/auth/signin - Login successful for email: ${email}`);
    return NextResponse.json(data);
  } catch (error) {
    console.error("POST /api/auth/signin - Error in /api/auth/signin:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

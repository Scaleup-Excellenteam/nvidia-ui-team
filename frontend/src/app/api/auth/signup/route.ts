import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { firstName, lastName, email, password } = body;

    // Mock signup logic - in a real app, you'd save to database
    console.log("Signup attempt:", { firstName, lastName, email });

    // Simulate successful registration
    return NextResponse.json({
      success: true,
      message: "User registered successfully",
      user: { email, firstName, lastName },
    });
  } catch (error) {
    console.error("Error in /api/auth/signup:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

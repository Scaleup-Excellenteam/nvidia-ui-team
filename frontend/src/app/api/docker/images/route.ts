import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      console.error(
        "GET /api/docker/images - Unauthorized access attempt - missing or invalid authorization header"
      );
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    console.log("GET /api/docker/images - Docker images requested");

    const backendUrl = process.env.BACKEND_API_URL || "http://localhost:8000";
    const response = await fetch(`${backendUrl}/docker/images`, {
      method: "GET",
      headers: {
        Authorization: authHeader,
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(
        `GET /api/docker/images - Failed to get docker images, status: ${response.status}`
      );
      return NextResponse.json(data, { status: response.status });
    }

    console.log(
      "GET /api/docker/images - Docker images retrieved successfully"
    );
    return NextResponse.json(data);
  } catch (error) {
    console.error(
      "GET /api/docker/images - Error in /api/docker/images:",
      error
    );
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

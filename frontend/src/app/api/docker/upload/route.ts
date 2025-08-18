import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      console.error(
        "POST /api/docker/upload - Unauthorized access attempt - missing or invalid authorization header"
      );
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    console.log("POST /api/docker/upload - Docker image upload requested");

    const backendUrl = process.env.BACKEND_API_URL || "http://localhost:8000";
    const response = await fetch(`${backendUrl}/docker/upload`, {
      method: "POST",
      headers: {
        Authorization: authHeader,
      },
      body: await request.formData(),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(
        `POST /api/docker/upload - Failed to upload docker image, status: ${response.status}`
      );
      return NextResponse.json(data, { status: response.status });
    }

    console.log("POST /api/docker/upload - Docker image uploaded successfully");
    return NextResponse.json(data);
  } catch (error) {
    console.error(
      "POST /api/docker/upload - Error in /api/docker/upload:",
      error
    );
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

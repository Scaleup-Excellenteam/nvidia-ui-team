import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest, context: unknown) {
  const { params } = context as { params: { id: string } };
  try {
    const authHeader = request.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      console.error(
        "POST /api/docker/images/[id]/stop - Unauthorized access attempt - missing or invalid authorization header"
      );
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    console.log(
      `POST /api/docker/images/${params.id}/stop - Stopping containers`
    );

    const backendUrl = process.env.BACKEND_API_URL || "http://localhost:8000";
    const response = await fetch(
      `${backendUrl}/docker/images/${params.id}/stop`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: authHeader,
        },
      }
    );

    if (response.ok) {
      const data = await response.json();
      return NextResponse.json(data);
    } else {
      const errorData = await response.json();
      console.error(
        `POST /api/docker/images/${params.id}/stop - Backend error:`,
        response.status,
        errorData
      );
      return NextResponse.json(errorData, { status: response.status });
    }
  } catch (error) {
    console.error(`POST /api/docker/images/${params.id}/stop - Error:`, error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

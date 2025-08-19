import { NextRequest, NextResponse } from "next/server";

export async function PUT(request: NextRequest, context: unknown) {
  const { params } = context as { params: { id: string } };
  try {
    const authHeader = request.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      console.error(
        "PUT /api/docker/images/[id]/resources - Unauthorized access attempt - missing or invalid authorization header"
      );
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    console.log(
      `PUT /api/docker/images/${params.id}/resources - Updating resources`
    );

    const backendUrl = process.env.BACKEND_API_URL || "http://localhost:8000";
    const response = await fetch(
      `${backendUrl}/docker/images/${params.id}/resources`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: authHeader,
        },
        body: JSON.stringify(body),
      }
    );

    if (response.ok) {
      const data = await response.json();
      return NextResponse.json(data);
    } else {
      const errorData = await response.json();
      console.error(
        `PUT /api/docker/images/${params.id}/resources - Backend error:`,
        response.status,
        errorData
      );
      return NextResponse.json(errorData, { status: response.status });
    }
  } catch (error) {
    console.error(
      `PUT /api/docker/images/${params.id}/resources - Error:`,
      error
    );
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

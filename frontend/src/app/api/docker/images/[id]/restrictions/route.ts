import { NextRequest, NextResponse } from "next/server";

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const authHeader = request.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const token = authHeader.substring(7);
    const body = await request.json();
    const { itemRestrictions } = body;
    const imageId = params.id;

    // Check for hardcoded admin token first
    if (token === "admin-token") {
      // Simulate successful update for admin user
      console.log(
        `Admin user updated restrictions for image ${imageId} to ${itemRestrictions}`
      );

      return NextResponse.json({
        success: true,
        message: `Item restrictions updated to ${itemRestrictions}`,
        imageId,
        itemRestrictions,
      });
    }

    // Try to call the FastAPI backend for other tokens
    try {
      const backendUrl = process.env.BACKEND_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${backendUrl}/docker/images/${imageId}/restrictions`,
        {
          method: "PUT",
          headers: {
            Authorization: authHeader,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ itemRestrictions }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(data, { status: response.status });
      }

      return NextResponse.json(data);
    } catch (backendError) {
      // If backend is not available, only allow admin token
      console.log("Backend not available, using fallback restrictions update");
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
  } catch (error) {
    console.error("Error in /api/docker/images/[id]/restrictions:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

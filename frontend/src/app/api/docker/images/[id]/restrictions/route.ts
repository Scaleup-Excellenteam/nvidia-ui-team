import { NextRequest, NextResponse } from "next/server";

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Get the authorization header
    const authHeader = request.headers.get("authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const token = authHeader.substring(7);

    // Only admin can update restrictions
    if (token !== "admin-token") {
      return NextResponse.json(
        { error: "Forbidden - Admin access required" },
        { status: 403 }
      );
    }

    const body = await request.json();
    const { itemRestrictions } = body;
    const imageId = params.id;

    // Mock update logic - in a real app, you'd update the database
    console.log(
      `Updating restrictions for image ${imageId} to ${itemRestrictions}`
    );

    return NextResponse.json({
      success: true,
      message: `Item restrictions updated to ${itemRestrictions}`,
      imageId,
      itemRestrictions,
    });
  } catch (error) {
    console.error("Error in /api/docker/images/[id]/restrictions:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

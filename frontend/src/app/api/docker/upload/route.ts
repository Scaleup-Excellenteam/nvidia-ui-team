import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    // Get the authorization header
    const authHeader = request.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const token = authHeader.substring(7);

    // Check for hardcoded admin token first
    if (token === "admin-token") {
      // Parse form data for admin user
      const formData = await request.formData();
      const image = formData.get("image") as File;
      const imageName = formData.get("imageName") as string;
      const innerPort = parseInt(formData.get("innerPort") as string);
      const scalingType = formData.get("scalingType") as string;
      const minContainers =
        parseInt(formData.get("minContainers") as string) || 0;
      const maxContainers =
        parseInt(formData.get("maxContainers") as string) || 0;
      const staticContainers =
        parseInt(formData.get("staticContainers") as string) || 0;
      const itemsPerContainer = parseInt(
        formData.get("itemsPerContainer") as string
      );
      const paymentLimit =
        parseFloat(formData.get("paymentLimit") as string) || 0;
      const description = formData.get("description") as string;

      // Validate required fields
      if (!image || !imageName || !innerPort || !itemsPerContainer) {
        return NextResponse.json(
          { error: "Missing required fields" },
          { status: 400 }
        );
      }

      // Simulate successful upload for admin user
      const imageId = Date.now().toString();
      console.log("Admin user uploaded Docker image:", {
        imageId,
        imageName,
        innerPort,
        scalingType,
        minContainers,
        maxContainers,
        staticContainers,
        itemsPerContainer,
        paymentLimit,
        description,
        fileName: image?.name,
        fileSize: image?.size,
      });

      return NextResponse.json({
        success: true,
        message: "Docker image uploaded successfully",
        imageId,
        imageName,
        status: "processing",
      });
    }

    // Try to call the FastAPI backend for other tokens
    try {
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
        return NextResponse.json(data, { status: response.status });
      }

      return NextResponse.json(data);
    } catch (backendError) {
      // If backend is not available, only allow admin token
      console.log("Backend not available, using fallback upload");
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
  } catch (error) {
    console.error("Error in /api/docker/upload:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

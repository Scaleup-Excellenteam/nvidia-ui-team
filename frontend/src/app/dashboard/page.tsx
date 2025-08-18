"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface DockerImage {
  id: number;
  image_name: string;
  image_tag: string;
  internal_port: number;
  min_containers: number;
  max_containers: number;
  cpu_limit: string;
  memory_limit: string;
  disk_limit: string;
  payment_limit: number;
  created_at: string;
  user_email: string;
  running_containers: number;
  total_containers: number;
  requests_per_second: number;
  total_requests: number;
  total_cost: number;
  cost_breakdown: any;
  healthy_containers: number;
  total_errors: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const [dockerImages, setDockerImages] = useState<DockerImage[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem("authToken");
    if (!token) {
      router.push("/signin");
      return;
    }

    // Check if user is admin (email = Admin, password = Admin)
    const checkAdminStatus = async () => {
      try {
        const response = await fetch("/api/auth/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const userData = await response.json();
          console.log("User data received:", userData);
          setUserEmail(userData.email);
          // Check for admin with case-insensitive comparison
          const isAdminUser =
            userData.email?.toLowerCase() === "admin@gmail.com" ||
            userData.email?.toLowerCase() === "admin";
          console.log("Is admin check:", isAdminUser, "Email:", userData.email);
          setIsAdmin(isAdminUser);
        }
      } catch (error) {
        console.error("Error checking user status:", error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAdminStatus();
  }, [router]);

  useEffect(() => {
    if (isAdmin) {
      // Fetch all docker images for admin
      fetchDockerImages();
    }
  }, [isAdmin]);

  const fetchDockerImages = async () => {
    try {
      const response = await fetch("/api/docker/images", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("authToken")}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Docker images data received:", data);
        console.log("Number of images:", data.images?.length || 0);

        // Deduplicate images based on ID
        const uniqueImages = data.images
          ? data.images.filter(
              (image: DockerImage, index: number, self: DockerImage[]) =>
                index ===
                self.findIndex((img: DockerImage) => img.id === image.id)
            )
          : [];

        console.log("Unique images after deduplication:", uniqueImages.length);
        setDockerImages(uniqueImages);
      }
    } catch (error) {
      console.error("Error fetching docker images:", error);
    }
  };

  const updateItemRestrictions = async (
    imageId: string,
    restrictions: number
  ) => {
    try {
      const response = await fetch(
        `/api/docker/images/${imageId}/restrictions`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("authToken")}`,
          },
          body: JSON.stringify({ itemRestrictions: restrictions }),
        }
      );

      if (response.ok) {
        fetchDockerImages(); // Refresh the list
      }
    } catch (error) {
      console.error("Error updating restrictions:", error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("authToken");
    router.push("/");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
              <p className="text-sm text-gray-600">Welcome, {userEmail}</p>
            </div>
            <div className="flex items-center space-x-4">
              {isAdmin && (
                <Link
                  href="/dashboard/health"
                  className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
                >
                  System Health
                </Link>
              )}
              <button
                onClick={handleLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload Section */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Upload Docker Image
          </h2>
          <p className="text-gray-600 mb-4">
            Upload your Docker image and configure container settings.
          </p>
          <Link
            href="/dashboard/upload"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Upload New Image
          </Link>
        </div>

        {/* Admin Section */}
        {isAdmin && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                All Docker Images
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Image Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Containers (Running/Total)
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Requests/sec
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total Cost
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Payment Limit
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Current Cost
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {dockerImages.map((image) => (
                    <tr key={image.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {image.image_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {image.running_containers} / {image.total_containers}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {image.requests_per_second
                          ? image.requests_per_second.toFixed(2)
                          : "N/A"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        $
                        {image.total_cost
                          ? image.total_cost.toFixed(2)
                          : "0.00"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        $
                        {image.payment_limit
                          ? image.payment_limit.toFixed(2)
                          : "0.00"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        $
                        {image.total_cost
                          ? image.total_cost.toFixed(2)
                          : "0.00"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            image.running_containers > 0
                              ? "bg-green-100 text-green-800"
                              : "bg-yellow-100 text-yellow-800"
                          }`}
                        >
                          {image.running_containers > 0 ? "Running" : "Stopped"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <button
                          onClick={() => {
                            if (image.total_errors > 0) {
                              alert(`Errors: ${image.total_errors}`);
                            } else {
                              alert("No errors for this image");
                            }
                          }}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          View Errors
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* User Section */}
        {!isAdmin && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Your Docker Images
            </h2>
            <p className="text-gray-600">
              You can upload and manage your Docker images. Contact admin for
              additional features.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

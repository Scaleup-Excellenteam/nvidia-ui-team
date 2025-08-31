"use client";

import { useState, useEffect, useRef } from "react";
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
  items_per_container: number;
  created_at: string;
  user_email: string;
  running_containers: number;
  total_containers: number;
  requests_per_second: number;
  total_requests: number;
  total_cost: number;
  cost_breakdown: Record<string, unknown>;
  healthy_containers: number;
  total_errors: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const [dockerImages, setDockerImages] = useState<DockerImage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isFetching, setIsFetching] = useState(false);
  const hasFetchedImagesRef = useRef(false);

  useEffect(() => {
    // Single-run: check auth, then if admin fetch images once
    const init = async () => {
      const token = localStorage.getItem("authToken");
      if (!token) {
        router.push("/signin");
        return;
      }

      try {
        const meRes = await fetch("/api/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (meRes.ok) {
          const userData = await meRes.json();
          setUserEmail(userData.email);
          const isAdminUser =
            userData.email?.toLowerCase() === "admin@gmail.com" ||
            userData.email?.toLowerCase() === "admin";
          setIsAdmin(isAdminUser);
          if (!hasFetchedImagesRef.current) {
            hasFetchedImagesRef.current = true; // guard before fetch
            await fetchDockerImages();
          }
        }
      } catch (error) {
        console.error("Error initializing dashboard:", error);
      } finally {
        setIsLoading(false);
      }
    };

    init();
    // empty dependency array ensures this runs once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchDockerImages = async () => {
    if (isFetching) {
      console.log("Already fetching images, skipping...");
      return;
    }

    try {
      setIsFetching(true);
      console.log("Fetching docker images...");
      const response = await fetch("/api/docker/images", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("authToken")}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Raw Docker images data received:", data);
        console.log("Number of images:", data.images?.length || 0);

        // Log each image individually to see duplicates
        if (data.images) {
          data.images.forEach((image: DockerImage, index: number) => {
            console.log(`Image ${index + 1}:`, {
              id: image.id,
              name: image.image_name,
              tag: image.image_tag,
              user: image.user_email,
            });
          });
        }

        // Deduplicate images based on ID
        const uniqueImages = data.images
          ? data.images.filter(
              (image: DockerImage, index: number, self: DockerImage[]) =>
                index ===
                self.findIndex((img: DockerImage) => img.id === image.id)
            )
          : [];

        console.log("Unique images after deduplication:", uniqueImages.length);
        console.log(
          "Final unique images:",
          uniqueImages.map((img: DockerImage) => ({
            id: img.id,
            name: img.image_name,
          }))
        );
        setDockerImages(uniqueImages);
      } else {
        console.error("Failed to fetch docker images:", response.status);
      }
    } catch (error) {
      console.error("Error fetching docker images:", error);
    } finally {
      setIsFetching(false);
    }
  };

  const handleSetPaymentLimit = async (image: DockerImage) => {
    const current = image.payment_limit ?? 0;
    const input = window.prompt(
      `Set payment limit for ${image.image_name} (current: $${current.toFixed(
        2
      )})`,
      String(current)
    );
    if (input === null) return;
    const newLimit = Number(input);
    if (Number.isNaN(newLimit) || newLimit < 0) {
      alert("Please enter a valid, non-negative number.");
      return;
    }
    try {
      const res = await fetch(`/api/docker/images/${image.id}/restrictions`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("authToken")}`,
        },
        body: JSON.stringify({ paymentLimit: newLimit }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.error("Failed to set payment limit", err);
        alert("Failed to update payment limit");
        return;
      }
      await fetchDockerImages();
    } catch (e) {
      console.error(e);
      alert("Failed to update payment limit");
    }
  };

  const handleSetResources = async (image: DockerImage) => {
    const current = image.items_per_container ?? 0;
    const input = window.prompt(
      `Set items per container for ${image.image_name} (current: ${current})`,
      String(current)
    );
    if (input === null) return;
    const newVal = Number(input);
    if (!Number.isInteger(newVal) || newVal <= 0) {
      alert("Please enter a valid positive integer.");
      return;
    }
    try {
      const res = await fetch(`/api/docker/images/${image.id}/restrictions`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("authToken")}`,
        },
        body: JSON.stringify({ itemRestrictions: newVal }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.error("Failed to set items per container", err);
        alert("Failed to update resources");
        return;
      }
      await fetchDockerImages();
    } catch (e) {
      console.error(e);
      alert("Failed to update resources");
    }
  };

  const handleStart = async (image: DockerImage) => {
    try {
      const res = await fetch(`/api/docker/images/${image.id}/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("authToken")}`,
        },
        body: JSON.stringify({ count: 1 }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.error("Failed to start container", err);
        alert("Failed to start container(s)");
        return;
      }
      await fetchDockerImages();
    } catch (e) {
      console.error(e);
      alert("Failed to start container(s)");
    }
  };

  const handleStop = async (image: DockerImage) => {
    try {
      const res = await fetch(`/api/docker/images/${image.id}/stop`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("authToken")}`,
        },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.error("Failed to stop containers", err);
        alert("Failed to stop containers");
        return;
      }
      await fetchDockerImages();
    } catch (e) {
      console.error(e);
      alert("Failed to stop containers");
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
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
        // Updated successfully; avoiding automatic refetch to prevent extra calls
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
                        <div className="flex gap-3 flex-wrap">
                          <button
                            onClick={() => handleSetPaymentLimit(image)}
                            className="inline-flex items-center px-3 py-1 rounded-md bg-yellow-100 text-yellow-800 hover:bg-yellow-200"
                          >
                            Set Limit
                          </button>
                          <button
                            onClick={() => handleSetResources(image)}
                            className="inline-flex items-center px-3 py-1 rounded-md bg-purple-100 text-purple-800 hover:bg-purple-200"
                          >
                            Set Resources
                          </button>
                          <button
                            onClick={() => handleStart(image)}
                            className="inline-flex items-center px-3 py-1 rounded-md bg-green-100 text-green-800 hover:bg-green-200"
                          >
                            Start +1
                          </button>
                          <button
                            onClick={() => handleStop(image)}
                            className="inline-flex items-center px-3 py-1 rounded-md bg-red-100 text-red-800 hover:bg-red-200"
                          >
                            Stop All
                          </button>
                        </div>
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
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                Your Docker Images
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
                      Payment Limit
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
                        {image.payment_limit
                          ? image.payment_limit.toFixed(2)
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
                        <div className="flex gap-3 flex-wrap">
                          <button
                            onClick={() => handleSetPaymentLimit(image)}
                            className="inline-flex items-center px-3 py-1 rounded-md bg-yellow-100 text-yellow-800 hover:bg-yellow-200"
                          >
                            Set Limit
                          </button>
                          <button
                            onClick={() => handleSetResources(image)}
                            className="inline-flex items-center px-3 py-1 rounded-md bg-purple-100 text-purple-800 hover:bg-purple-200"
                          >
                            Set Resources
                          </button>
                          <button
                            onClick={() => handleStart(image)}
                            className="inline-flex items-center px-3 py-1 rounded-md bg-green-100 text-green-800 hover:bg-green-200"
                          >
                            Start +1
                          </button>
                          <button
                            onClick={() => handleStop(image)}
                            className="inline-flex items-center px-3 py-1 rounded-md bg-red-100 text-red-800 hover:bg-red-200"
                          >
                            Stop All
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

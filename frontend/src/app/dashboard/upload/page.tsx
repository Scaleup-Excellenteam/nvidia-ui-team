"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

type ScalingType = "minimal" | "maximal" | "static";

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const [formData, setFormData] = useState({
    imageName: "",
    innerPort: 8080,
    scalingType: "static" as ScalingType,
    minContainers: 1,
    maxContainers: 5,
    staticContainers: 2,
    itemsPerContainer: 100,
    paymentLimit: 50.0, // New field for payment limit
    description: "",
  });

  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      // Auto-fill image name from filename
      const nameWithoutExtension = file.name.replace(/\.[^/.]+$/, "");
      setFormData((prev) => ({ ...prev, imageName: nameWithoutExtension }));
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        name === "innerPort" ||
        name === "minContainers" ||
        name === "maxContainers" ||
        name === "staticContainers" ||
        name === "itemsPerContainer"
          ? parseInt(value) || 0
          : name === "paymentLimit"
          ? parseFloat(value) || 0
          : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile) {
      alert("Please select a Docker image file");
      return;
    }

    setIsLoading(true);
    setUploadProgress(0);

    try {
      // Create FormData for file upload
      const formDataToSend = new FormData();
      formDataToSend.append("image", selectedFile);
      formDataToSend.append("imageName", formData.imageName);
      formDataToSend.append("innerPort", formData.innerPort.toString());
      formDataToSend.append("scalingType", formData.scalingType);
      formDataToSend.append("minContainers", formData.minContainers.toString());
      formDataToSend.append("maxContainers", formData.maxContainers.toString());
      formDataToSend.append(
        "staticContainers",
        formData.staticContainers.toString()
      );
      formDataToSend.append(
        "itemsPerContainer",
        formData.itemsPerContainer.toString()
      );
      formDataToSend.append("paymentLimit", formData.paymentLimit.toString());
      formDataToSend.append("description", formData.description);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await fetch("/api/docker/upload", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("authToken")}`,
        },
        body: formDataToSend,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Upload failed");
      }

      const data = await response.json();
      console.log("Upload successful:", data);

      // Redirect to dashboard after successful upload
      setTimeout(() => {
        router.push("/dashboard");
      }, 1000);
    } catch (error) {
      console.error("Upload error:", error);
      alert(
        error instanceof Error
          ? error.message
          : "Upload failed. Please try again."
      );
    } finally {
      setIsLoading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <Link
                href="/dashboard"
                className="text-blue-600 hover:text-blue-500"
              >
                ← Back to Dashboard
              </Link>
              <h1 className="text-3xl font-bold text-gray-900">
                Upload Docker Image
              </h1>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* File Upload Section */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Docker Image File
              </label>
              <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                <div className="space-y-1 text-center">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    stroke="currentColor"
                    fill="none"
                    viewBox="0 0 48 48"
                  >
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <div className="flex justify-center text-sm text-gray-600">
                    <label
                      htmlFor="file-upload"
                      className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                    >
                      <span>Upload a file</span>
                      <input
                        id="file-upload"
                        name="file-upload"
                        type="file"
                        className="sr-only"
                        accept=".tar,.tar.gz,.tgz"
                        onChange={handleFileSelect}
                        ref={fileInputRef}
                      />
                    </label>
                  </div>
                  <p className="text-xs text-gray-500">
                    TAR, TAR.GZ, TGZ up to 10MB
                  </p>
                  {selectedFile && (
                    <p className="text-sm text-green-600">
                      Selected: {selectedFile.name}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Image Configuration */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="imageName"
                  className="block text-sm font-medium text-gray-700"
                >
                  Image Name
                </label>
                <input
                  type="text"
                  id="imageName"
                  name="imageName"
                  value={formData.imageName}
                  onChange={handleInputChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="my-docker-image"
                  required
                />
              </div>

              <div>
                <label
                  htmlFor="innerPort"
                  className="block text-sm font-medium text-gray-700"
                >
                  Internal Port
                </label>
                <input
                  type="number"
                  id="innerPort"
                  name="innerPort"
                  value={formData.innerPort}
                  onChange={handleInputChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  min="1"
                  max="65535"
                  required
                />
              </div>
            </div>

            {/* Scaling Configuration */}
            <div>
              <label
                htmlFor="scalingType"
                className="block text-sm font-medium text-gray-700"
              >
                Scaling Type
              </label>
              <select
                id="scalingType"
                name="scalingType"
                value={formData.scalingType}
                onChange={handleInputChange}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="minimal">Minimal Containers</option>
                <option value="maximal">Maximal Containers</option>
                <option value="static">Static Amount</option>
              </select>
            </div>

            {/* Container Configuration */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
              {formData.scalingType === "minimal" && (
                <div>
                  <label
                    htmlFor="minContainers"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Minimum Containers
                  </label>
                  <input
                    type="number"
                    id="minContainers"
                    name="minContainers"
                    value={formData.minContainers}
                    onChange={handleInputChange}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    min="1"
                    required
                  />
                </div>
              )}

              {formData.scalingType === "maximal" && (
                <div>
                  <label
                    htmlFor="maxContainers"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Maximum Containers
                  </label>
                  <input
                    type="number"
                    id="maxContainers"
                    name="maxContainers"
                    value={formData.maxContainers}
                    onChange={handleInputChange}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    min="1"
                    required
                  />
                </div>
              )}

              {formData.scalingType === "static" && (
                <div>
                  <label
                    htmlFor="staticContainers"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Static Containers
                  </label>
                  <input
                    type="number"
                    id="staticContainers"
                    name="staticContainers"
                    value={formData.staticContainers}
                    onChange={handleInputChange}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    min="1"
                    required
                  />
                </div>
              )}

              <div>
                <label
                  htmlFor="itemsPerContainer"
                  className="block text-sm font-medium text-gray-700"
                >
                  Resources per Container
                </label>
                <input
                  type="number"
                  id="itemsPerContainer"
                  name="itemsPerContainer"
                  value={formData.itemsPerContainer}
                  onChange={handleInputChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  min="1"
                  required
                />
              </div>
            </div>

            {/* Payment Limit */}
            <div>
              <label
                htmlFor="paymentLimit"
                className="block text-sm font-medium text-gray-700"
              >
                Payment Limit per Image ($)
              </label>
              <input
                type="number"
                id="paymentLimit"
                name="paymentLimit"
                value={formData.paymentLimit}
                onChange={handleInputChange}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                min="0"
                step="0.01"
                required
              />
              <p className="mt-1 text-sm text-gray-500">
                Service will be stopped when this limit is reached
              </p>
            </div>

            {/* Description */}
            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium text-gray-700"
              >
                Description (Optional)
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={3}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe your Docker image..."
              />
            </div>

            {/* Upload Progress */}
            {isLoading && (
              <div>
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Uploading...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex justify-end space-x-4">
              <Link
                href="/dashboard"
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={isLoading || !selectedFile}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? "Uploading..." : "Upload Image"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

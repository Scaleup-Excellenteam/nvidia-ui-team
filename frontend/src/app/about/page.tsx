export default function AboutPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow-lg rounded-lg p-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-6">About Us</h1>

          <div className="prose prose-lg max-w-none">
            <p className="text-gray-600 mb-4">
              Welcome to our Next.js application! This is an example page that
              demonstrates how to create new pages in the App Router
              architecture.
            </p>

            <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">
              How Pages Work
            </h2>

            <p className="text-gray-600 mb-4">
              In Next.js App Router, pages are created by adding{" "}
              <code className="bg-gray-100 px-2 py-1 rounded">page.tsx</code>{" "}
              files inside folders within the{" "}
              <code className="bg-gray-100 px-2 py-1 rounded">src/app/</code>{" "}
              directory.
            </p>

            <ul className="list-disc list-inside text-gray-600 space-y-2">
              <li>
                <code className="bg-gray-100 px-2 py-1 rounded">
                  src/app/page.tsx
                </code>{" "}
                → Home page (/)
              </li>
              <li>
                <code className="bg-gray-100 px-2 py-1 rounded">
                  src/app/about/page.tsx
                </code>{" "}
                → About page (/about)
              </li>
              <li>
                <code className="bg-gray-100 px-2 py-1 rounded">
                  src/app/contact/page.tsx
                </code>{" "}
                → Contact page (/contact)
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

import Link from "next/link"

export default function Page() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 p-4">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">
        CADGen AI
      </h1>
      <p className="text-lg text-gray-600">
        Text-to-3D CAD Platform
      </p>
      <div className="mt-8 flex gap-4">
        <Link
          href="/health"
          className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          Health Check
        </Link>
      </div>
    </main>
  )
}

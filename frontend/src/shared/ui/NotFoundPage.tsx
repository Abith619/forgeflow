
import { Link } from 'react-router';

export function NotFoundPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="mt-3 text-slate-600">Page not found.</p>

      <Link
        to="/"
        className="mt-6 rounded-lg bg-blue-600 px-5 py-3 text-white hover:bg-blue-700"
      >
        Return to Dashboard
      </Link>
    </main>
  );
}

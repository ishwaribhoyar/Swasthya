import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';
import { ROUTES } from '@/utils/constants';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <div className="text-center">
        <span className="text-6xl mb-4 block">🩺</span>
        <h1 className="text-4xl font-bold text-slate-900 mb-2">404</h1>
        <h2 className="text-xl font-semibold text-slate-700 mb-6">Page not found</h2>
        <p className="text-slate-500 mb-8 max-w-md mx-auto">
          The page you are looking for doesn't exist or has been moved to another URL.
        </p>
        <Link
          to={ROUTES.DASHBOARD}
          className="inline-flex items-center gap-2 bg-primary text-white px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors shadow-sm"
        >
          <Home className="w-5 h-5" />
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}

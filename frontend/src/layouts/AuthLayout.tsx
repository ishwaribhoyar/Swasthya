import { Outlet } from 'react-router-dom';

export default function AuthLayout() {
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-background">
      <div className="hidden md:flex flex-1 bg-primary text-primary-foreground items-center justify-center p-12">
        <div className="max-w-md space-y-6">
          <div className="flex items-center space-x-3">
            <span className="text-4xl">🏥</span>
            <h1 className="text-4xl font-bold tracking-tight">ClinIQ</h1>
          </div>
          <p className="text-xl opacity-90 leading-relaxed">
            Intelligent healthcare management for modern medical professionals. Streamline patient care, analytics, and records.
          </p>
        </div>
      </div>
      <div className="flex-1 flex items-center justify-center p-6 md:p-12">
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

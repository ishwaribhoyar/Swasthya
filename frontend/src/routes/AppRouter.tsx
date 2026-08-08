import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ROUTES } from '@/utils/constants';
import PrivateRoute from './PrivateRoute';
import PublicRoute from './PublicRoute';
import AuthLayout from '@/layouts/AuthLayout';
import AppLayout from '@/layouts/AppLayout';

// Pages
import LoginPage from '@/features/auth/LoginPage';
import RegisterPage from '@/features/auth/RegisterPage';
import DashboardPage from '@/features/dashboard/DashboardPage';
import PatientsPage from '@/features/patients/PatientsPage';
import PatientDetailPage from '@/features/patients/PatientDetailPage';
import TimelinePage from '@/features/timeline/TimelinePage';
import AnalyticsPage from '@/features/analytics/AnalyticsPage';
import AssistantPage from '@/features/assistant/AssistantPage';
import SettingsPage from '@/features/settings/SettingsPage';
import NotFoundPage from '@/features/NotFoundPage';

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
        
        {/* Public Routes */}
        <Route element={<PublicRoute><AuthLayout /></PublicRoute>}>
          <Route path={ROUTES.LOGIN} element={<LoginPage />} />
          <Route path={ROUTES.REGISTER} element={<RegisterPage />} />
        </Route>

        {/* Private Routes */}
        <Route element={<PrivateRoute><AppLayout /></PrivateRoute>}>
          <Route path={ROUTES.DASHBOARD} element={<DashboardPage />} />
          <Route path={ROUTES.PATIENTS} element={<PatientsPage />} />
          <Route path={`${ROUTES.PATIENTS}/:id`} element={<PatientDetailPage />} />
          <Route path={ROUTES.TIMELINE} element={<TimelinePage />} />
          <Route path={ROUTES.ANALYTICS} element={<AnalyticsPage />} />
          <Route path={ROUTES.ASSISTANT} element={<AssistantPage />} />
          <Route path={ROUTES.SETTINGS} element={<SettingsPage />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}

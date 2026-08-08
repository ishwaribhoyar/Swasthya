/**
 * Root Application Component
 * Wraps the router in necessary global context providers.
 */
import { AuthProvider } from './contexts/AuthContext';
import { GlobalProvider } from './contexts/GlobalContext';
import { LoadingProvider } from './contexts/LoadingContext';
import { ErrorProvider } from './contexts/ErrorContext';
import AppRouter from './routes/AppRouter';

export default function App() {
  return (
    <ErrorProvider>
      <LoadingProvider>
        <AuthProvider>
          <GlobalProvider>
            <AppRouter />
          </GlobalProvider>
        </AuthProvider>
      </LoadingProvider>
    </ErrorProvider>
  );
}

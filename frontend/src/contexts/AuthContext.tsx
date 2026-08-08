/**
 * AuthContext
 *
 * Manages authentication state for the entire application.
 * Real JWT authentication backed by FastAPI & SQLite.
 * Every user is a Clinician.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { IUser, IAuthTokens, ILoginRequest } from '@/types/auth';
import client from '@/services/api/client';

// ─── Context Shape ────────────────────────────────────────────────────────────

interface AuthContextType {
  /** Authenticated clinician. Null when not logged in. */
  user: IUser | null;
  /** JWT token pair. Null when not logged in. */
  tokens: IAuthTokens | null;
  /** True only when user and tokens are both present and valid. */
  isAuthenticated: boolean;
  /** True while the initial token-validation check is in progress. */
  isLoading: boolean;
  /** Call this to authenticate. Throws on failure. */
  login: (credentials: ILoginRequest) => Promise<void>;
  /** Clears all auth state and persisted tokens. */
  logout: () => void;
  /** Silently exchanges a refresh token for a new access token. */
  refreshToken: () => Promise<void>;
}

// ─── Context ──────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ─── Storage Keys ─────────────────────────────────────────────────────────────

const ACCESS_TOKEN_KEY  = 'cliniq_access_token';
const REFRESH_TOKEN_KEY = 'cliniq_refresh_token';

// ─── Provider ─────────────────────────────────────────────────────────────────

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user,      setUser]      = useState<IUser | null>(null);
  const [tokens,    setTokens]    = useState<IAuthTokens | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Clears all authentication state.
   */
  const clearSession = useCallback(() => {
    setUser(null);
    setTokens(null);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }, []);

  /**
   * Persists a token pair and user into state and localStorage.
   */
  const persistSession = useCallback((authUser: IUser, authTokens: IAuthTokens) => {
    setUser(authUser);
    setTokens(authTokens);
    if (authTokens.accessToken && authTokens.accessToken !== 'undefined') {
      localStorage.setItem(ACCESS_TOKEN_KEY, authTokens.accessToken);
    }
    if (authTokens.refreshToken && authTokens.refreshToken !== 'undefined') {
      localStorage.setItem(REFRESH_TOKEN_KEY, authTokens.refreshToken);
    }
  }, []);

  /**
   * On mount: restore any previously persisted tokens and fetch /auth/me profile.
   */
  useEffect(() => {
    const accessToken  = localStorage.getItem(ACCESS_TOKEN_KEY);
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

    if (accessToken && accessToken !== 'undefined' && refreshToken && refreshToken !== 'undefined') {
      setTokens({ accessToken, refreshToken });
      client
        .get('/auth/me')
        .then((res: any) => {
          const userData = res.data || res;
          setUser({
            id: userData.id,
            email: userData.email,
            firstName: userData.first_name,
            lastName: userData.last_name,
          });
        })
        .catch(() => {
          clearSession();
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      clearSession();
      setIsLoading(false);
    }

    const handleUnauthorized = () => {
      clearSession();
      setIsLoading(false);
    };

    window.addEventListener('cliniq_unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('cliniq_unauthorized', handleUnauthorized);
    };
  }, [clearSession]);

  const login = async (credentials: ILoginRequest): Promise<void> => {
    try {
      const res: any = await client.post('/auth/login', credentials);
      const tokenData = res.data || res;
      const accessToken = tokenData.access_token;
      const refreshToken = tokenData.refresh_token;
      const rawUser = tokenData.user;

      if (!accessToken) {
        throw new Error('Invalid login response from server.');
      }

      const authUser: IUser = {
        id: rawUser?.id || '1',
        email: rawUser?.email || credentials.email,
        firstName: rawUser?.first_name || 'Clinician',
        lastName: rawUser?.last_name || '',
      };
      persistSession(authUser, { accessToken, refreshToken });
    } catch (err: any) {
      throw new Error(err?.message || 'Authentication failed. Please check your credentials.');
    }
  };

  /**
   * logout — immediately clears all session data.
   */
  const logout = (): void => {
    client.post('/auth/logout').catch(() => {});
    clearSession();
  };

  const refreshToken = async (): Promise<void> => {
    if (!tokens?.refreshToken) {
      clearSession();
      return;
    }
    try {
      const res: any = await client.post('/auth/refresh', { refresh_token: tokens.refreshToken });
      const data = res.data || res;
      const newAccess = data.access_token;
      setTokens({ accessToken: newAccess, refreshToken: tokens.refreshToken });
      localStorage.setItem(ACCESS_TOKEN_KEY, newAccess);
    } catch {
      clearSession();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        tokens,
        isAuthenticated: !!user && !!tokens,
        isLoading,
        login,
        logout,
        refreshToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// ─── Consumer Hook ────────────────────────────────────────────────────────────

export const useAuthContext = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
};

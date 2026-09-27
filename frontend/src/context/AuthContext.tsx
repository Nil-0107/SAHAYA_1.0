import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { isAxiosError } from "axios";
import { authApi, type AuthSession } from "../services/authApi";
import { setAccessToken, setAuthSessionListener } from "../services/api";
import type { AuthUser } from "../types";

interface LoginCredentials {
  identifier: string;
  password: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  sessionExpired: boolean;
  bootstrapError: string;
  login: (credentials: LoginCredentials) => Promise<AuthUser>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<AuthUser>;
  adoptSignup: (session: AuthSession, fullName: string) => void;
  pendingFullName: string;
  clearPendingFullName: () => void;
  clearAuthState: () => void;
  dismissAuthError: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [pendingFullName, setPendingFullName] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);
  const [bootstrapError, setBootstrapError] = useState("");

  const applySession = useCallback((session: AuthSession) => {
    setAccessToken(session.access_token);
    setUser(session.user);
    setSessionExpired(false);
    setBootstrapError("");
  }, []);

  const clearAuthState = useCallback(() => {
    setAccessToken(null);
    setUser(null);
    setPendingFullName("");
    setBootstrapError("");
  }, []);

  useEffect(() => {
    setAuthSessionListener({
      onSessionRefreshed: applySession,
      onSessionExpired: () => {
        clearAuthState();
        setSessionExpired(true);
      },
    });

    let active = true;
    authApi
      .refresh()
      .then((session) => {
        if (active) applySession(session);
      })
      .catch((caught: unknown) => {
        if (!active) return;
        clearAuthState();
        if (!isAxiosError(caught) || caught.response?.status !== 401) {
          setBootstrapError("The server is unavailable. Please try signing in again.");
        }
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
      setAuthSessionListener(null);
    };
  }, [applySession, clearAuthState]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const session = await authApi.login(credentials);
    setPendingFullName("");
    applySession(session);
    return session.user;
  }, [applySession]);

  const refreshUser = useCallback(async () => {
    const currentUser = await authApi.me();
    setUser(currentUser);
    return currentUser;
  }, []);

  const adoptSignup = useCallback((session: AuthSession, fullName: string) => {
    setPendingFullName(fullName.trim());
    applySession(session);
  }, [applySession]);

  const clearPendingFullName = useCallback(() => setPendingFullName(""), []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Local credentials are cleared even if the server is temporarily unavailable.
    } finally {
      clearAuthState();
      setSessionExpired(false);
    }
  }, [clearAuthState]);

  const dismissAuthError = useCallback(() => setBootstrapError(""), []);

  const value = useMemo(
    () => ({
      user,
      isLoading,
      sessionExpired,
      bootstrapError,
      login,
      logout,
      refreshUser,
      adoptSignup,
      pendingFullName,
      clearPendingFullName,
      clearAuthState,
      dismissAuthError,
    }),
    [
      user,
      isLoading,
      sessionExpired,
      bootstrapError,
      login,
      logout,
      refreshUser,
      adoptSignup,
      pendingFullName,
      clearPendingFullName,
      clearAuthState,
      dismissAuthError,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}

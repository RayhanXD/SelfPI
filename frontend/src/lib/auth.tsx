import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, githubLoginUrl, setSessionToken } from "./api";
import type { AuthUser, MeResponse } from "../types/api";

interface AuthState {
  loading: boolean;
  authenticated: boolean;
  oauthConfigured: boolean;
  loginRequired: boolean;
  user: AuthUser | null;
  /** Default login URL → lands on /app after OAuth. */
  loginUrl: string | null;
  /** Login URL that returns to a specific SPA path after OAuth. */
  loginHrefFor: (next?: string) => string;
  reload: () => Promise<MeResponse | null>;
  applySession: (me: MeResponse, sessionToken?: string | null) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const applySession = useCallback((data: MeResponse, sessionToken?: string | null) => {
    if (sessionToken) setSessionToken(sessionToken);
    setMe(data);
    setLoading(false);
  }, []);

  const reload = useCallback(async () => {
    try {
      const data = await api.getMe();
      setMe(data);
      return data;
    } catch {
      const fallback: MeResponse = {
        authenticated: false,
        oauth_configured: false,
        login_required: false,
        user: null,
        login_url: null,
      };
      setMe(fallback);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      setSessionToken(null);
      await reload();
    }
  }, [reload]);

  const loginHrefFor = useCallback((next: string = "/app") => githubLoginUrl(next), []);

  const value = useMemo<AuthState>(
    () => ({
      loading,
      authenticated: Boolean(me?.authenticated),
      oauthConfigured: Boolean(me?.oauth_configured),
      loginRequired: Boolean(me?.login_required),
      user: me?.user ?? null,
      loginUrl: me?.oauth_configured || me?.login_url ? githubLoginUrl("/app") : null,
      loginHrefFor,
      reload,
      applySession,
      logout,
    }),
    [loading, me, reload, logout, loginHrefFor, applySession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

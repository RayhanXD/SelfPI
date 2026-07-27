import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, resolveApiUrl } from "./api";
import type { AuthUser, MeResponse } from "../types/api";

interface AuthState {
  loading: boolean;
  authenticated: boolean;
  oauthConfigured: boolean;
  loginRequired: boolean;
  user: AuthUser | null;
  loginUrl: string | null;
  reload: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    try {
      const data = await api.getMe();
      setMe(data);
    } catch {
      setMe({
        authenticated: false,
        oauth_configured: false,
        login_required: false,
        user: null,
        login_url: null,
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const logout = useCallback(async () => {
    await api.logout();
    await reload();
  }, [reload]);

  const value = useMemo<AuthState>(
    () => ({
      loading,
      authenticated: Boolean(me?.authenticated),
      oauthConfigured: Boolean(me?.oauth_configured),
      loginRequired: Boolean(me?.login_required),
      user: me?.user ?? null,
      loginUrl: resolveApiUrl(me?.login_url ?? "/auth/github/login"),
      reload,
      logout,
    }),
    [loading, me, reload, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

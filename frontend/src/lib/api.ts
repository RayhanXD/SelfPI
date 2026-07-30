import type {
  ApiSummary,
  ChangeDetail,
  ChangeListResponse,
  ChangeSummary,
  ConnectedRepo,
  DetectApisResponse,
  ListInstallationReposResponse,
  HandoffResponse,
  InstallationSyncResponse,
  MeResponse,
  SettingsResponse,
} from "../types/api";

/** API origin from Vite env. Empty in local dev (Vite proxy). Absolute in prod. */
export function apiOrigin(): string {
  const raw = import.meta.env.VITE_API_URL as string | undefined;
  return (raw ?? "").replace(/\/$/, "");
}

/** Resolve a relative API path (or pass through absolute URLs). */
export function resolveApiUrl(pathOrUrl: string): string {
  if (/^https?:\/\//i.test(pathOrUrl)) return pathOrUrl;
  const path = pathOrUrl.startsWith("/") ? pathOrUrl : `/${pathOrUrl}`;
  return `${apiOrigin()}${path}`;
}

/** Safe post-login SPA path (same-origin relative only). */
export function sanitizeNextPath(next: string | null | undefined, fallback = "/app"): string {
  const path = (next ?? "").trim();
  if (!path.startsWith("/") || path.startsWith("//") || path.includes("\\")) {
    return fallback;
  }
  if (path.startsWith("/auth/")) return fallback;
  return path;
}

/**
 * Full browser URL for Login with GitHub.
 * After GitHub auth the API redirects to `/auth/callback` then the SPA lands on `next`.
 */
export function githubLoginUrl(next: string = "/app"): string {
  const dest = sanitizeNextPath(next, "/app");
  const base = resolveApiUrl("/auth/github/login");
  const sep = base.includes("?") ? "&" : "?";
  return `${base}${sep}next=${encodeURIComponent(dest)}`;
}

const BEARER_KEY = "selfpi_session_token";

export function getSessionToken(): string | null {
  try {
    return sessionStorage.getItem(BEARER_KEY);
  } catch {
    return null;
  }
}

export function setSessionToken(token: string | null): void {
  try {
    if (token) sessionStorage.setItem(BEARER_KEY, token);
    else sessionStorage.removeItem(BEARER_KEY);
  } catch {
    /* private mode / blocked storage */
  }
}

const DEFAULT_TIMEOUT_MS = 12_000;

async function request<T>(
  path: string,
  init?: RequestInit & { timeoutMs?: number },
): Promise<T> {
  const controller = new AbortController();
  const timeoutMs =
    typeof init?.timeoutMs === "number" ? init.timeoutMs : DEFAULT_TIMEOUT_MS;
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const { timeoutMs: _ignored, signal: userSignal, ...rest } = init ?? {};
    if (userSignal) {
      if (userSignal.aborted) controller.abort();
      else userSignal.addEventListener("abort", () => controller.abort(), { once: true });
    }
    const bearer = getSessionToken();
    const res = await fetch(resolveApiUrl(path), {
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}),
        ...(rest.headers ?? {}),
      },
      ...rest,
      signal: controller.signal,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      const message =
        body?.error?.message ??
        (typeof body?.detail === "object" ? body.detail?.error?.message : null) ??
        res.statusText;
      throw new Error(message || `HTTP ${res.status}`);
    }
    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("API request timed out — the backend may be waking up. Try again.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  listApis: () => request<ApiSummary[]>("/apis"),
  getApi: (id: string) => request<ApiSummary>(`/apis/${id}`),
  getSettings: () => request<SettingsResponse>("/settings"),
  getMe: () => request<MeResponse>("/auth/me"),
  completeHandoff: (handoff: string) =>
    request<HandoffResponse>("/auth/handoff", {
      method: "POST",
      body: JSON.stringify({ handoff }),
    }),
  logout: () => request<{ logged_out: boolean }>("/auth/logout", { method: "POST" }),
  syncInstallation: () =>
    request<InstallationSyncResponse>("/auth/github/sync-installation", {
      method: "POST",
    }),
  listRepos: () => request<ListInstallationReposResponse>("/repos"),
  getConnectedRepo: () => request<ConnectedRepo | null>("/repos/connected"),
  connectRepo: (full_name: string, repo_path?: string | null) =>
    request<ConnectedRepo>("/repos/connect", {
      method: "POST",
      // Connect runs checkout + API detection; allow longer than default.
      timeoutMs: 90_000,
      body: JSON.stringify({
        full_name,
        ...(repo_path != null ? { repo_path } : {}),
      }),
    }),
  disconnectRepo: () =>
    request<{ disconnected: boolean }>("/repos/connected", { method: "DELETE" }),
  detectApis: () =>
    request<DetectApisResponse>("/repos/connected/detect", { method: "POST" }),
  checkApi: (id: string) =>
    request<{
      checked: boolean;
      new_version: string | null;
      changes_detected: number;
      baseline?: boolean;
      unchanged?: boolean;
    }>(`/apis/${id}/check`, { method: "POST" }),
  pushSpecVersion: (id: string, version: string, spec: object) =>
    request<{ version: string; changes_detected: number }>(`/apis/${id}/spec-versions`, {
      method: "POST",
      body: JSON.stringify({ version, spec }),
    }),
  listChanges: (params?: { api_id?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.api_id) q.set("api_id", params.api_id);
    if (params?.status) q.set("status", params.status);
    const qs = q.toString();
    return request<ChangeListResponse>(`/changes${qs ? `?${qs}` : ""}`);
  },
  getChange: (id: string) => request<ChangeDetail>(`/changes/${id}`),
  dismissChange: (id: string) =>
    request<ChangeSummary>(`/changes/${id}/dismiss`, { method: "POST" }),
  rescanChange: (id: string) =>
    request<{ call_site_count: number; status: string }>(`/changes/${id}/rescan`, {
      method: "POST",
    }),
  openPr: (id: string) =>
    request<ChangeSummary>(`/changes/${id}/open-pr`, { method: "POST" }),
};

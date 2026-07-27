import type {
  ApiSummary,
  ChangeDetail,
  ChangeListResponse,
  ChangeSummary,
  ConnectedRepo,
  ListInstallationReposResponse,
  MeResponse,
  SettingsResponse,
} from "../types/api";

const BASE = "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
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
}

export const api = {
  listApis: () => request<ApiSummary[]>("/apis"),
  getApi: (id: string) => request<ApiSummary>(`/apis/${id}`),
  getSettings: () => request<SettingsResponse>("/settings"),
  getMe: () => request<MeResponse>("/auth/me"),
  logout: () => request<{ logged_out: boolean }>("/auth/logout", { method: "POST" }),
  listRepos: () => request<ListInstallationReposResponse>("/repos"),
  getConnectedRepo: () => request<ConnectedRepo | null>("/repos/connected"),
  connectRepo: (full_name: string, repo_path?: string | null) =>
    request<ConnectedRepo>("/repos/connect", {
      method: "POST",
      body: JSON.stringify({
        full_name,
        ...(repo_path != null ? { repo_path } : {}),
      }),
    }),
  disconnectRepo: () =>
    request<{ disconnected: boolean }>("/repos/connected", { method: "DELETE" }),
  checkApi: (id: string) =>
    request<{ checked: boolean; new_version: string | null; changes_detected: number }>(
      `/apis/${id}/check`,
      { method: "POST" },
    ),
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

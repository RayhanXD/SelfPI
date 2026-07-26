import type { ApiSummary, ChangeDetail, ChangeListResponse } from "../types/api";

const BASE = "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Accept: "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.error?.message ?? res.statusText;
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listApis: () => request<ApiSummary[]>("/apis"),
  getApi: (id: string) => request<ApiSummary>(`/apis/${id}`),
  checkApi: (id: string) =>
    request<{ checked: boolean; new_version: string | null; changes_detected: number }>(
      `/apis/${id}/check`,
      { method: "POST" },
    ),
  listChanges: (params?: { api_id?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (params?.api_id) q.set("api_id", params.api_id);
    if (params?.status) q.set("status", params.status);
    const qs = q.toString();
    return request<ChangeListResponse>(`/changes${qs ? `?${qs}` : ""}`);
  },
  getChange: (id: string) => request<ChangeDetail>(`/changes/${id}`),
  dismissChange: (id: string) =>
    request(`/changes/${id}/dismiss`, { method: "POST" }),
  rescanChange: (id: string) =>
    request(`/changes/${id}/rescan`, { method: "POST" }),
};

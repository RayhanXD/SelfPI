import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api } from "./api";
import type { ConnectedRepo, SettingsResponse } from "../types/api";

interface WorkspaceState {
  /** Monotonic counter — bump after connect/switch/disconnect so pages reload. */
  revision: number;
  connectedRepo: string | null;
  settings: SettingsResponse | null;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
  /** Bind a repo as the workspace target (also used to switch). */
  switchRepo: (full_name: string) => Promise<ConnectedRepo>;
  disconnect: () => Promise<void>;
  notifyChanged: (connectedRepo?: string | null) => void;
}

const WorkspaceContext = createContext<WorkspaceState | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [revision, setRevision] = useState(0);
  const [connectedRepo, setConnectedRepo] = useState<string | null>(null);
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const next = await api.getSettings();
      setSettings(next);
      setConnectedRepo(next.connected_repo ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workspace");
      setSettings(null);
      setConnectedRepo(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload, revision]);

  const notifyChanged = useCallback((next?: string | null) => {
    if (next !== undefined) setConnectedRepo(next);
    setRevision((r) => r + 1);
  }, []);

  const switchRepo = useCallback(
    async (full_name: string) => {
      const doc = await api.connectRepo(full_name);
      setConnectedRepo(doc.full_name);
      setRevision((r) => r + 1);
      return doc;
    },
    [],
  );

  const disconnect = useCallback(async () => {
    await api.disconnectRepo();
    setConnectedRepo(null);
    setRevision((r) => r + 1);
  }, []);

  const value = useMemo<WorkspaceState>(
    () => ({
      revision,
      connectedRepo,
      settings,
      loading,
      error,
      reload,
      switchRepo,
      disconnect,
      notifyChanged,
    }),
    [
      revision,
      connectedRepo,
      settings,
      loading,
      error,
      reload,
      switchRepo,
      disconnect,
      notifyChanged,
    ],
  );

  return (
    <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error("useWorkspace must be used within WorkspaceProvider");
  return ctx;
}

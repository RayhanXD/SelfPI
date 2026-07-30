/** Shared types — mirrors docs/API_CONTRACT.md (snake_case). */

export type ApiStatus =
  | "up_to_date"
  | "change_detected"
  | "breaking_change_unhandled";

export type ChangeStatus =
  | "detected"
  | "scanning"
  | "pr_open"
  | "merged"
  | "dismissed";

export type ChangeKind =
  | "removed_field"
  | "renamed_param"
  | "type_changed"
  | "value_deprecated";

export type SourceLayer = "grep" | "structural" | "agent";

export type PrState = "open" | "merged" | "closed";

export interface ApiSummary {
  id: string;
  name: string;
  current_version: string | null;
  status: ApiStatus;
  languages: string[];
  last_checked: string | null;
  open_change_count: number;
  repo?: string | null;
  spec_url?: string | null;
  /** "demo" = Bump spec; "live" = Check now */
  mode?: "demo" | "live" | string | null;
  /** "detected" | "manual" | "seed" — how the watched API was created */
  source?: string | null;
}

export interface SettingsResponse {
  github_configured: boolean;
  default_base_branch: string;
  repo_path_set: boolean;
  hint?: string | null;
  connected_repo?: string | null;
  watch_interval_seconds?: number;
  watch_enabled?: boolean;
  oauth_configured?: boolean;
  login_required?: boolean;
  authenticated?: boolean;
  user?: AuthUser | null;
  login_url?: string | null;
  /** True when this user (or env fallback) has an App installation id */
  app_installed?: boolean;
  /** https://github.com/apps/{slug}/installations/new */
  install_url?: string | null;
}

export interface AuthUser {
  id?: number | null;
  login: string;
  name?: string | null;
  avatar_url?: string | null;
  html_url?: string | null;
}

export interface MeResponse {
  authenticated: boolean;
  oauth_configured: boolean;
  login_required: boolean;
  user: AuthUser | null;
  login_url?: string | null;
  app_installed?: boolean;
  install_url?: string | null;
}

export interface HandoffResponse extends MeResponse {
  session_token: string;
}

export interface InstallationSyncResponse {
  app_installed: boolean;
  install_url?: string | null;
  installation_id?: string | null;
}

export interface ConnectedRepo {
  full_name: string;
  owner: string;
  name: string;
  default_branch?: string | null;
  html_url?: string | null;
  private?: boolean | null;
  repo_path?: string | null;
  connected_at?: string | null;
  /** Filled by POST /repos/connect after auto-detect */
  detected_apis?: string[] | null;
  /** Catalog hits with no public OpenAPI URL yet */
  unwatchable?: string[] | null;
}

export interface DetectApisResponse {
  detected_apis: string[];
  ensured: string[];
  unwatchable?: string[];
  repo_path?: string | null;
  full_name?: string | null;
}

export interface InstallationRepo {
  full_name: string;
  owner: string;
  name: string;
  private: boolean;
  default_branch: string;
  html_url?: string | null;
  connected: boolean;
}

export interface ListInstallationReposResponse {
  items: InstallationRepo[];
  connected_repo?: string | null;
}

export interface PrSummary {
  number: number;
  url?: string | null;
  state: PrState;
  tests_passing?: boolean | null;
  opened_at?: string | null;
}

export interface ChangeSummary {
  id: string;
  api_id: string;
  operation_id: string;
  kind: ChangeKind;
  detail: Record<string, unknown>;
  call_site_count: number;
  status: ChangeStatus;
  pr: PrSummary | null;
  detected_at: string | null;
}

export interface CallSite {
  file: string;
  span: { start_line: number; end_line: number };
  language: string;
  receiver?: string | null;
  path: string[];
  invoked: boolean;
  operation_id?: string | null;
  args: Array<{
    name?: string | null;
    value?: string | null;
    value_kind?: string | null;
    kind: string;
  }>;
  import?: { module: string; symbol?: string | null } | null;
  alias?: string | null;
  in_comment: boolean;
  snippet?: string | null;
  source_layer?: SourceLayer | null;
  confidence?: number | null;
}

export interface ChangeDetail extends Omit<ChangeSummary, "call_site_count"> {
  from_version?: string | null;
  to_version?: string | null;
  repo?: string | null;
  spec_diff?: {
    operation_id: string;
    removed: string[];
    added: string[];
    raw?: string | null;
  } | null;
  call_sites: CallSite[];
}

export interface ChangeListResponse {
  items: ChangeSummary[];
  next_cursor: string | null;
}

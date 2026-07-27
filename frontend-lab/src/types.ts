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
  mode?: "demo" | "live" | string | null;
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
  args: Array<{ name?: string | null; kind: string }>;
  snippet?: string | null;
  source_layer?: SourceLayer | null;
  confidence?: number | null;
  in_comment: boolean;
}

export interface ChangeDetail extends Omit<ChangeSummary, "call_site_count"> {
  from_version?: string | null;
  to_version?: string | null;
  repo?: string | null;
  detail: Record<string, unknown>;
  spec_diff?: {
    operation_id: string;
    removed: string[];
    added: string[];
    raw?: string | null;
  } | null;
  call_sites: CallSite[];
  patch_preview?: string | null;
  explanation?: string | null;
}

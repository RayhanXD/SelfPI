import type { ApiStatus, ChangeStatus, SourceLayer } from "../types";

export function apiStatusLabel(status: ApiStatus): string {
  switch (status) {
    case "up_to_date":
      return "Up to date";
    case "change_detected":
      return "Change detected";
    case "breaking_change_unhandled":
      return "Breaking change unhandled";
  }
}

export function apiStatusTone(status: ApiStatus): "ok" | "warn" | "danger" {
  switch (status) {
    case "up_to_date":
      return "ok";
    case "change_detected":
      return "warn";
    case "breaking_change_unhandled":
      return "danger";
  }
}

export function changeStatusLabel(status: ChangeStatus): string {
  switch (status) {
    case "detected":
      return "Detected";
    case "scanning":
      return "Scanning";
    case "pr_open":
      return "PR open";
    case "merged":
      return "Merged";
    case "dismissed":
      return "Dismissed";
  }
}

export function changeStatusTone(
  status: ChangeStatus,
): "ok" | "warn" | "danger" | "info" | "muted" {
  switch (status) {
    case "merged":
      return "ok";
    case "pr_open":
      return "info";
    case "dismissed":
      return "muted";
    case "scanning":
    case "detected":
      return "warn";
  }
}

export function confidenceTone(confidence: number): "ok" | "warn" | "danger" {
  if (confidence >= 0.85) return "ok";
  if (confidence >= 0.6) return "warn";
  return "danger";
}

export function layerLabel(layer: SourceLayer): string {
  return layer;
}

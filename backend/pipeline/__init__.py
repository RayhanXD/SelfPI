"""Pipeline package — wire diff/scanner/adjudicator/patcher into persistence."""

from pipeline.process import process_breaking_change, process_spec_bump, rescan_change, resolve_repo_path

__all__ = [
    "process_breaking_change",
    "process_spec_bump",
    "rescan_change",
    "resolve_repo_path",
]

"""Pipeline package — wire diff/scanner/adjudicator/patcher into persistence."""

from pipeline.process import (
    open_change_pr,
    process_breaking_change,
    process_spec_bump,
    rescan_change,
    resolve_repo_path,
)

__all__ = [
    "open_change_pr",
    "process_breaking_change",
    "process_spec_bump",
    "rescan_change",
    "resolve_repo_path",
]

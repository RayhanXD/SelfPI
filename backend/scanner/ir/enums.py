"""Shared status / enum values — must match docs/API_CONTRACT.md."""

from enum import Enum


class ApiStatus(str, Enum):
    UP_TO_DATE = "up_to_date"
    CHANGE_DETECTED = "change_detected"
    BREAKING_CHANGE_UNHANDLED = "breaking_change_unhandled"


class ChangeStatus(str, Enum):
    DETECTED = "detected"
    SCANNING = "scanning"
    PR_OPEN = "pr_open"
    MERGED = "merged"
    DISMISSED = "dismissed"


class ChangeKind(str, Enum):
    REMOVED_FIELD = "removed_field"
    RENAMED_PARAM = "renamed_param"
    TYPE_CHANGED = "type_changed"
    VALUE_DEPRECATED = "value_deprecated"


class SourceLayer(str, Enum):
    GREP = "grep"
    STRUCTURAL = "structural"
    AGENT = "agent"


class PrState(str, Enum):
    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"


class ArgKind(str, Enum):
    KEYWORD = "keyword"
    POSITIONAL = "positional"
    OBJECT_FIELD = "object-field"
    STRUCT_FIELD = "struct-field"


class ValueKind(str, Enum):
    LITERAL = "literal"
    DYNAMIC = "dynamic"

"""Python language module — lexing rules + surface→operation_id map (v1).

Adding a language = adding a module under languages/. Don't scatter lang logic
through the pipeline (CLAUDE.md golden rule 5).
"""

from __future__ import annotations

from typing import Any

# Surface method paths → canonical OpenAPI operationId (Decision 1).
# Expand as the Stripe Python SDK surface is mapped.
SURFACE_TO_OPERATION: dict[tuple[str, ...], str] = {
    ("Charge", "create"): "createCharge",
    ("Charge", "retrieve"): "retrieveCharge",
    ("Customer", "create"): "createCustomer",
    ("PaymentIntent", "create"): "createPaymentIntent",
}

LANGUAGE = "python"

# Lexing hints for the tokenizer (M2 fills these in).
COMMENT_PREFIXES = ("#",)
STRING_DELIMITERS = ('"', "'", '"""', "'''")
IDENTIFIER_PATTERN = r"[A-Za-z_][A-Za-z0-9_]*"


def resolve_operation_id(path: list[str]) -> str | None:
    """Map a member-access path to a canonical operation_id."""
    return SURFACE_TO_OPERATION.get(tuple(path))


def tokenize(source: str) -> list[dict[str, Any]]:
    """Lex Python source. Implemented in M2."""
    raise NotImplementedError("Python tokenizer — implement in M2")

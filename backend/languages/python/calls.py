"""Extract CallSite records from a Python token stream + import table."""

from __future__ import annotations

import hashlib
from typing import Any

from languages.python.imports import Binding
from languages.python import resolve_operation_id
from scanner.ir.enums import ArgKind, ValueKind
from scanner.ir.types import Arg, CallSite, ImportRef, Span


def extract_call_sites(
    tokens: list[dict[str, Any]],
    *,
    file: str,
    language: str,
    imports: dict[str, Binding],
    source: str | None = None,
) -> list[CallSite]:
    """Find receiver.path(...) call shapes; skip comment/string contexts."""
    sites: list[CallSite] = []
    lines = source.splitlines() if source is not None else None
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]
        if tok.get("in_comment") or tok.get("in_string"):
            i += 1
            continue
        if tok["type"] != "IDENT":
            i += 1
            continue

        # Parse IDENT ( DOT IDENT )* LPAREN
        chain_start = i
        parts = [tok["value"]]
        j = i + 1
        while j + 1 < n and tokens[j]["type"] == "DOT" and tokens[j + 1]["type"] == "IDENT":
            if tokens[j].get("in_comment") or tokens[j + 1].get("in_comment"):
                break
            parts.append(tokens[j + 1]["value"])
            j += 2

        if j >= n or tokens[j]["type"] != "LPAREN":
            i += 1
            continue
        if tokens[j].get("in_comment"):
            i += 1
            continue

        # Need at least receiver.member (path non-empty after receiver)
        if len(parts) < 2:
            i += 1
            continue

        receiver_name = parts[0]
        path = parts[1:]
        binding = imports.get(receiver_name)

        # Resolve aliased root: import stripe as s → receiver canonical "stripe"
        if binding is not None:
            if binding.symbol is None:
                receiver = binding.module
                alias = binding.alias
                import_ref = ImportRef(module=binding.module, symbol=None)
            else:
                # from stripe import Charge → Charge.create(...)
                receiver = binding.module
                path = [binding.symbol, *path]
                alias = binding.alias
                import_ref = ImportRef(module=binding.module, symbol=binding.symbol)
        else:
            # Unresolved — still emit for recall; scorer will down-rank
            receiver = receiver_name
            alias = None
            import_ref = None

        lparen = tokens[j]
        args, end_idx = _parse_args(tokens, j + 1)
        if end_idx is None:
            i += 1
            continue

        rparen = tokens[end_idx]
        start_line = tokens[chain_start]["line"]
        end_line = rparen["line"]
        snippet = None
        if lines is not None and 1 <= start_line <= len(lines):
            snippet = lines[start_line - 1].strip()

        op_id = resolve_operation_id(path)
        span = Span(
            start_line=start_line,
            end_line=end_line,
            start_col=tokens[chain_start]["col"],
            end_col=rparen["col"] + 1,
        )
        site_id = _stable_id(file, span.start_line, span.end_line, span.start_col)

        sites.append(
            CallSite(
                id=site_id,
                file=file,
                span=span,
                language=language,
                receiver=receiver,
                path=path,
                invoked=True,
                args=args,
                operation_id=op_id,
                **{"import": import_ref},
                alias=alias,
                in_comment=False,
                in_string=False,
                in_test_file=_is_test_file(file),
                snippet=snippet,
            )
        )
        i = end_idx + 1

    return sites


def _parse_args(tokens: list[dict[str, Any]], start: int) -> tuple[list[Arg], int | None]:
    """Parse argument list until matching RPAREN. Returns (args, rparen_index)."""
    args: list[Arg] = []
    i = start
    n = len(tokens)
    depth = 1
    pos = 0

    while i < n:
        tok = tokens[i]
        if tok.get("in_comment"):
            i += 1
            continue
        if tok["type"] == "LPAREN":
            depth += 1
            i += 1
            continue
        if tok["type"] == "RPAREN":
            depth -= 1
            if depth == 0:
                return args, i
            i += 1
            continue
        if depth != 1:
            i += 1
            continue
        if tok["type"] == "COMMA":
            i += 1
            continue
        if tok["type"] == "NEWLINE":
            i += 1
            continue

        # keyword: IDENT EQ value
        if (
            tok["type"] == "IDENT"
            and i + 1 < n
            and tokens[i + 1]["type"] == "EQ"
        ):
            name = tok["value"]
            value_toks, next_i = _read_value(tokens, i + 2)
            value_text = "".join(t["value"] for t in value_toks)
            value_kind = _classify_value(value_toks)
            args.append(
                Arg(
                    name=name,
                    value=value_text or None,
                    value_kind=value_kind,
                    kind=ArgKind.KEYWORD,
                    pos=pos,
                )
            )
            pos += 1
            i = next_i
            continue

        # positional value
        value_toks, next_i = _read_value(tokens, i)
        if not value_toks:
            i += 1
            continue
        value_text = "".join(t["value"] for t in value_toks)
        args.append(
            Arg(
                name=None,
                value=value_text or None,
                value_kind=_classify_value(value_toks),
                kind=ArgKind.POSITIONAL,
                pos=pos,
            )
        )
        pos += 1
        i = next_i

    return args, None


def _read_value(tokens: list[dict[str, Any]], start: int) -> tuple[list[dict[str, Any]], int]:
    """Read one argument value expression until COMMA/RPAREN at depth 0 of this arg."""
    i = start
    n = len(tokens)
    depth = 0
    collected: list[dict[str, Any]] = []

    while i < n:
        tok = tokens[i]
        if tok.get("in_comment"):
            i += 1
            continue
        if tok["type"] == "NEWLINE" and depth == 0 and collected:
            break
        if tok["type"] in ("LPAREN", "LBRACKET", "LBRACE"):
            depth += 1
            collected.append(tok)
            i += 1
            continue
        if tok["type"] in ("RPAREN", "RBRACKET", "RBRACE"):
            if depth == 0:
                break
            depth -= 1
            collected.append(tok)
            i += 1
            continue
        if tok["type"] == "COMMA" and depth == 0:
            break
        collected.append(tok)
        i += 1

    return collected, i


def _classify_value(value_toks: list[dict[str, Any]]) -> ValueKind:
    if len(value_toks) == 1 and value_toks[0]["type"] in ("STRING", "NUMBER"):
        return ValueKind.LITERAL
    if len(value_toks) == 1 and value_toks[0]["type"] == "KEYWORD" and value_toks[0]["value"] in (
        "None",
        "True",
        "False",
    ):
        return ValueKind.LITERAL
    return ValueKind.DYNAMIC


def _stable_id(file: str, start_line: int, end_line: int, start_col: int | None) -> str:
    raw = f"{file}:{start_line}:{end_line}:{start_col or 0}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def _is_test_file(file: str) -> bool:
    name = file.replace("\\", "/").split("/")[-1]
    return name.startswith("test_") or name.endswith("_test.py") or "/tests/" in file.replace("\\", "/")

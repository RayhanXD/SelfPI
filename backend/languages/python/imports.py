"""Import / alias pre-pass over a Python token stream (design Decision 3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Binding:
    """Maps a local name to the imported module (and optional symbol)."""

    module: str
    symbol: str | None = None
    alias: str | None = None  # local name if aliased; else None


def build_import_table(tokens: list[dict[str, Any]]) -> dict[str, Binding]:
    """Walk import statements and build local-name → Binding table.

    Supports:
      import stripe
      import stripe as s
      from stripe import Charge
      from stripe import Charge as C
    """
    table: dict[str, Binding] = {}
    i = 0
    n = len(tokens)

    def skip_newlines(idx: int) -> int:
        while idx < n and tokens[idx]["type"] == "NEWLINE":
            idx += 1
        return idx

    while i < n:
        tok = tokens[i]
        if tok.get("in_comment") or tok.get("in_string"):
            i += 1
            continue

        # import module [as alias]
        if tok["type"] == "KEYWORD" and tok["value"] == "import":
            i += 1
            i = skip_newlines(i)
            if i >= n or tokens[i]["type"] != "IDENT":
                continue
            module = tokens[i]["value"]
            i += 1
            # dotted: import stripe.something — keep first segment as module root for v1
            while i < n and tokens[i]["type"] == "DOT":
                i += 1
                if i < n and tokens[i]["type"] == "IDENT":
                    module = module + "." + tokens[i]["value"]
                    i += 1
            alias = None
            local = module.split(".")[0]
            if i < n and tokens[i]["type"] == "KEYWORD" and tokens[i]["value"] == "as":
                i += 1
                if i < n and tokens[i]["type"] == "IDENT":
                    alias = tokens[i]["value"]
                    local = alias
                    i += 1
            table[local] = Binding(module=module.split(".")[0], symbol=None, alias=alias)
            continue

        # from module import name [as alias]
        if tok["type"] == "KEYWORD" and tok["value"] == "from":
            i += 1
            i = skip_newlines(i)
            if i >= n or tokens[i]["type"] != "IDENT":
                continue
            module = tokens[i]["value"]
            i += 1
            while i < n and tokens[i]["type"] == "DOT":
                i += 1
                if i < n and tokens[i]["type"] == "IDENT":
                    module = module + "." + tokens[i]["value"]
                    i += 1
            if i >= n or not (tokens[i]["type"] == "KEYWORD" and tokens[i]["value"] == "import"):
                continue
            i += 1
            i = skip_newlines(i)
            # one or more names separated by commas
            while i < n:
                if tokens[i]["type"] != "IDENT":
                    break
                symbol = tokens[i]["value"]
                i += 1
                local = symbol
                alias = None
                if i < n and tokens[i]["type"] == "KEYWORD" and tokens[i]["value"] == "as":
                    i += 1
                    if i < n and tokens[i]["type"] == "IDENT":
                        alias = tokens[i]["value"]
                        local = alias
                        i += 1
                table[local] = Binding(module=module.split(".")[0], symbol=symbol, alias=alias)
                if i < n and tokens[i]["type"] == "COMMA":
                    i += 1
                    continue
                break
            continue

        i += 1

    return table

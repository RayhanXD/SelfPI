"""Language modules registry."""

from languages import python as python_lang
from languages import typescript as typescript_lang

REGISTRY = {
    "python": python_lang,
    "typescript": typescript_lang,
}


def get_language(name: str):
    try:
        return REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Unknown language module: {name}") from exc

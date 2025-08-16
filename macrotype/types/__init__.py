from __future__ import annotations

"""Type analysis pipeline with parsing and unparsing."""

import typing

from .ir import Ty
from .normalize import norm
from .parse import parse
from .resolve import ResolveEnv, resolve
from .unparse import unparse, unparse_top
from .validate import validate


def from_type(obj: object) -> Ty:
    """Parse, resolve, normalize, and validate *obj* into a :class:`Ty`."""
    parsed = parse(obj)
    resolved = resolve(parsed, ResolveEnv(module="", imports={}))
    normalized = norm(resolved)
    return validate(normalized)


def normalize_annotation(obj: object) -> object:
    """Return a normalized typing object for *obj*.

    The annotation is parsed, resolved, normalized, validated, and then
    converted back into a Python typing object.
    """

    if obj is typing.NoReturn:
        # ``NoReturn`` should be preserved rather than normalized to ``Never``
        return typing.NoReturn
    return unparse_top(from_type(obj))


__all__ = [
    "Ty",
    "from_type",
    "unparse",
    "unparse_top",
    "parse",
    "resolve",
    "norm",
    "validate",
    "normalize_annotation",
]

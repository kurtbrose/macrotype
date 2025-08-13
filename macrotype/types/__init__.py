from __future__ import annotations

"""Type analysis pipeline with parsing and unparsing."""

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


__all__ = ["Ty", "from_type", "unparse", "unparse_top", "parse", "resolve", "norm", "validate"]

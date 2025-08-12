from __future__ import annotations

"""Type analysis and emission pipeline."""

from typing import cast

from .emit import EmitCtx, emit
from .ir import Ty
from .normalize import norm
from .parse import parse
from .resolve import ResolveEnv, resolve
from .validate import validate


def from_type(obj: object) -> Ty:
    """Parse, resolve, normalize, and validate *obj* into a :class:`Ty`."""
    parsed = parse(obj)
    resolved = resolve(parsed, ResolveEnv(module="", imports={}))
    normalized = norm(resolved)
    validated = validate(normalized)
    return cast(Ty, validated)


__all__ = ["Ty", "from_type", "emit", "EmitCtx", "parse", "resolve", "norm", "validate"]

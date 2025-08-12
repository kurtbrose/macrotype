from typing import Any

from .emit import EmitCtx, emit
from .ir import Ty
from .normalize import norm
from .parse import parse
from .resolve import ResolveEnv, resolve
from .validate import validate


def from_type(obj: object) -> Ty: ...

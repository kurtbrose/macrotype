# Generated via: macrotype macrotype/types macrotype/modules/emit.py
# Do not edit by hand
from typing import Literal

from macrotype.types.ir import Ty, TyApp, TyRoot

EllipsisType = ellipsis

class TypeValidationError(TypeError): ...

Context = Literal

def validate(t: NormalizedTy) -> TyRoot: ...
def _v(
    node: Ty, *, ctx: Literal["top", "tuple_items", "call_params", "concat_args", "other"]
) -> None: ...
def _validate_literal_value(v: object) -> None: ...
def _validate_concatenate(node: TyApp) -> None: ...

# Generated via: macrotype macrotype
# Do not edit by hand
from macrotype.types.ir import Ty, TyApp, TyRoot
from typing import Literal, Literal

EllipsisType = ellipsis

class TypeValidationError(TypeError): ...

Context = Literal

def validate(t: NormalizedTy) -> TyRoot: ...

def _v(node: Ty, *, ctx: Literal['top', 'tuple_items', 'call_params', 'concat_args', 'other']) -> None: ...

def _validate_literal_value(v: object) -> None: ...

def _validate_concatenate(node: TyApp) -> None: ...

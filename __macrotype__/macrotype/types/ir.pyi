# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations

import enum
from dataclasses import dataclass
from enum import Enum
from types import EllipsisType
from typing import ClassVar, Literal, NewType

@dataclass(frozen=True, kw_only=True, slots=True)
class TyAnnoTree:
    annos: tuple[object, ...]
    child: None | TyAnnoTree
    def flatten(self) -> tuple[object, ...]: ...

@dataclass(frozen=True, kw_only=True, slots=True)
class TyRoot:
    ty: None | Ty  # None here for bare Final
    annotations: None | TyAnnoTree
    is_final: bool
    is_required: None | bool
    is_classvar: bool

@dataclass(frozen=True, kw_only=True, slots=True)
class Ty:
    annotations: None | TyAnnoTree
    is_generic: ClassVar[bool]
    @property
    def base_type(self) -> None | type: ...
    @property
    def generic_args(self) -> tuple["Ty", ...]: ...
    @property
    def union_types(self) -> tuple["Ty", ...]: ...

@dataclass(frozen=True, kw_only=True, slots=True)
class TyAny(Ty): ...

@dataclass(frozen=True, kw_only=True, slots=True)
class TyNever(Ty): ...

@dataclass(frozen=True, kw_only=True, slots=True)
class TyType(Ty):
    type_: type
    @property
    def base_type(self) -> type: ...

@dataclass(frozen=True, kw_only=True, slots=True)
class TyApp(Ty):
    base: Ty
    args: tuple[Ty, ...]
    is_generic: ClassVar[bool]
    @property
    def base_type(self) -> None | type: ...
    @property
    def generic_args(self) -> tuple[Ty, ...]: ...

@dataclass(frozen=True, kw_only=True, slots=True)
class TyUnion(Ty):
    options: tuple[Ty, ...]
    @property
    def union_types(self) -> tuple[Ty, ...]: ...

LitPrim = int | bool | str | bytes | None | enum.Enum

LitVal = int | bool | str | bytes | None | enum.Enum | tuple["LitVal", ...]

@dataclass(frozen=True, kw_only=True, slots=True)
class TyLiteral(Ty):
    values: tuple[Enum | None | bool | bytes | int | str | tuple["LitVal", ...], ...]

@dataclass(frozen=True, kw_only=True, slots=True)
class TyCallable(Ty):
    params: EllipsisType | tuple[Ty, ...]
    ret: Ty

@dataclass(frozen=True, kw_only=True, slots=True)
class TyForward(Ty):
    qualname: str

@dataclass(frozen=True, kw_only=True, slots=True)
class TyTypeVar(Ty):
    name: str
    bound: None | Ty
    constraints: tuple[Ty, ...]
    cov: bool
    contrav: bool

@dataclass(frozen=True, kw_only=True, slots=True)
class TyParamSpec(Ty):
    name: str
    flavor: Literal["args", "kwargs"] | None

@dataclass(frozen=True, kw_only=True, slots=True)
class TyTypeVarTuple(Ty):
    name: str

@dataclass(frozen=True, kw_only=True, slots=True)
class TyUnpack(Ty):
    inner: Ty

def has_type_member(ty: Ty, members: set[type]) -> bool: ...
def strip_type_members(ty: Ty, members: set[type]) -> Ty: ...

ParsedTy = NewType("ParsedTy", TyRoot)  # output of parse.parse

ResolvedTy = NewType("ResolvedTy", TyRoot)  # output of resolve.resolve

NormalizedTy = NewType("NormalizedTy", TyRoot)  # output of normalize.norm

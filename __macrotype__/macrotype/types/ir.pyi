# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, NewType, TyAnnoTree

annotations = annotations

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

@dataclass(frozen=True, kw_only=True, slots=True)
class TyAny(Ty): ...

@dataclass(frozen=True, kw_only=True, slots=True)
class TyNever(Ty): ...

@dataclass(frozen=True, kw_only=True, slots=True)
class TyType(Ty):
    type_: type

@dataclass(frozen=True, kw_only=True, slots=True)
class TyApp(Ty):
    base: Ty
    args: tuple[Ty, ...]

@dataclass(frozen=True, kw_only=True, slots=True)
class TyUnion(Ty):
    options: tuple[Ty, ...]

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

ParsedTy = NewType("ParsedTy", TyRoot)  # output of parse.parse

ResolvedTy = NewType("ResolvedTy", TyRoot)  # output of resolve.resolve

NormalizedTy = NewType("NormalizedTy", TyRoot)  # output of normalize.norm

# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from macrotype.types.ir import ParsedTy, Ty, TyAnnoTree, TyRoot, TyTypeVar

from typing import NewType

annotations = annotations

LitVal = int | bool | str | bytes | None | enum.Enum | tuple['LitVal', ...]

ParsedTy = NewType("ParsedTy", TyRoot)

_TYPING_ATTR_TYPES: tuple[type, ...]

@dataclass(frozen=True)
class ParseEnv:
    module: None | str
    typevars: dict[str, TyTypeVar]  # name -> TyTypeVar
    in_typed_dict: bool  # lets callers capture Required/NotRequired
    def get_tv(self, name: str) -> None | TyTypeVar: ...

def _tytype_of(obj: object) -> Ty: ...

def _maybe_to_ir(tp: None | object, env: None | ParseEnv) -> None | Ty: ...

def _litval_of(val: object) -> Enum | None | bool | bytes | int | str | tuple['LitVal', ...]: ...

def _origin_args(tp: object) -> tuple[None | object, tuple[object, ...]]: ...

def _cached[T](f: 'T') -> 'T': ...

_to_ir = _cached.<locals>.wrapped

def _push_ann(tree: None | TyAnnoTree, ann: object) -> tuple[None | TyAnnoTree, object]: ...

def _append_ann_child(tree: None | TyAnnoTree, child: None | TyAnnoTree) -> None | TyAnnoTree: ...

def parse_root(tp: object, env: None | ParseEnv) -> TyRoot: ...

def parse(tp: object, env: None | ParseEnv) -> ParsedTy: ...

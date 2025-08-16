# Generated via: macrotype tests/annotations.py -o tests/annotations.pyi
# Do not edit by hand
# pyright: basic
# mypy: allow-any-expr
from typing import Any, NewType, ParamSpec, TypeVar, TypeVarTuple

T = TypeVar("T")

P = ParamSpec("P")

Ts = TypeVarTuple("Ts")

U = TypeVar("U")

NumberLike = TypeVar("NumberLike")

CovariantT = TypeVar("CovariantT", covariant=True)

ContravariantT = TypeVar("ContravariantT", contravariant=True)

TDV = TypeVar("TDV")

UserId = NewType("UserId", int)

def strip_null(ann: Any, null: Any) -> Any: ...

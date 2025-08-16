# pyright: basic
# mypy: allow-any-expr
import types
import typing
from typing import Any, NewType, ParamSpec, TypeVar, TypeVarTuple

T = TypeVar("T")
P = ParamSpec("P")
Ts = TypeVarTuple("Ts")
# Bound type variable ensures bound metadata is ignored
U = TypeVar("U", bound=str)
# Constrained type variable ensures constraint metadata is ignored
NumberLike = TypeVar("NumberLike", int, float)
CovariantT = TypeVar("CovariantT", covariant=True)
ContravariantT = TypeVar("ContravariantT", contravariant=True)
TDV = TypeVar("TDV")
UserId = NewType("UserId", int)


def strip_null(ann: Any, null: Any) -> Any:
    origin = typing.get_origin(ann)
    if origin in {typing.Union, types.UnionType}:
        args = [a for a in typing.get_args(ann) if a is not null]
        if not args:
            return null
        result = args[0]
        for a in args[1:]:
            result |= a
        return result
    return ann


# Callable wrapped by non-function object with __wrapped__
def _wrap(fn):
    class Wrapper:
        def __init__(self, f):
            self._f = f
            self.__wrapped__ = f

        def __call__(self, *a, **kw):
            return self._f(*a, **kw)

    return Wrapper(fn)


@_wrap
def wrapped_callable(x: int, y: str) -> str: ...

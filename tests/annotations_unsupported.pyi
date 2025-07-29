# Generated via: manual separation of unsupported features
# These declarations use syntax from PEP 695 that mypy fails to parse.
from typing import NewType, ParamSpec, TypeVar, TypeVarTuple

T = TypeVar("T")
P = ParamSpec("P")
Ts = TypeVarTuple("Ts")
U = TypeVar("U")
NumberLike = TypeVar("NumberLike")
UserId = NewType("UserId", int)

def use_params(*args: P.args, **kwargs: P.kwargs) -> int: ...

InferredT = TypeVar("InferredT", infer_variance=True)

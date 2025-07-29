# These annotations use syntax standardized in PEP 695 but unsupported by mypy.
# Each example below includes a comment describing the unsupported feature.

from typing import NewType, ParamSpec, TypeVar, TypeVarTuple

T = TypeVar("T")
P = ParamSpec("P")
Ts = TypeVarTuple("Ts")
U = TypeVar("U")
NumberLike = TypeVar("NumberLike")
UserId = NewType("UserId", int)


# Function using ``P.args`` and ``P.kwargs`` requires PEP 695 generics
# which mypy doesn't yet support.
def use_params(*args: P.args, **kwargs: P.kwargs) -> int:
    return 0


# ``TypeVar`` with the ``infer_variance`` parameter from PEP 695 is not yet
# implemented by mypy.
InferredT = TypeVar("InferredT", infer_variance=True)

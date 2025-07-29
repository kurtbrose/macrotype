# These annotations use syntax standardized in PEP 695 but unsupported by mypy.
# Each example below includes a comment describing the unsupported feature.

from typing import (
    Callable,
    NewType,
    ParamSpec,
    TypeAlias,
    TypeVar,
    TypeVarTuple,
    overload,
)

T = TypeVar("T")
P = ParamSpec("P")
Ts = TypeVarTuple("Ts")
U = TypeVar("U")
NumberLike = TypeVar("NumberLike")
UserId = NewType("UserId", int)

# PEP 695 type alias syntax is not yet recognized by mypy.
MyList: TypeAlias = list[int]
# Uses "type" statement for an alias
# (mypy fails to parse `type` statement)
type StrList = list[str]

# Chain of generic type aliases using PEP 695 syntax
# mypy cannot parse generic aliases defined with `type`.
type Alias0[T] = list[T]
# Alias referencing another generic alias
# still unsupported due to PEP 695 syntax
type Alias1[T] = Alias0[T]

# Additional alias shapes demonstrating various type parameters
# All still rely on PEP 695 syntax which mypy rejects.
type AliasNewType = UserId
# Simple TypeVar alias
# unsupported due to PEP 695
type AliasTypeVar[T] = T
# Union alias
# uses `type` syntax unsupported by mypy
type AliasUnion = int | str
# Alias with generic union
# PEP 695 syntax unsupported
type ListOrSet[T] = list[T] | set[T]
# Alias using ParamSpec
# Not supported because mypy can't parse PEP 695 aliases with **P
type IntFunc[**P] = Callable[P, int]
# Alias with TypeVarTuple
# mypy doesn't understand star-unpack in PEP 695 aliases yet
type LabeledTuple[*Ts] = tuple[str, *Ts]
# Recursive alias
# mypy can't handle recursive aliases with PEP 695 syntax
type RecursiveList[T] = T | list[RecursiveList[T]]


# PEP 695 generic class syntax is entirely unsupported by mypy.
class NewGeneric[T]:
    value: T

    def get(self) -> T:
        return self.value


# Class with explicit bound on type parameter
class BoundClass[T: int]:
    value: T


# Class with constrained type parameter
class ConstrainedClass[T: (int, str)]:
    value: T


# Overloads generated dynamically in a loop are tricky for mypy's resolver.
for typ in (bytes, bytearray):

    @overload
    def loop_over(x: typ) -> str: ...


del typ


def loop_over(x: bytes | bytearray) -> str:
    return str(x)


# Function using ``P.args`` and ``P.kwargs`` requires PEP 695 generics
# which mypy doesn't yet support.
def use_params(*args: P.args, **kwargs: P.kwargs) -> int:
    return 0


# ``TypeVar`` with the ``infer_variance`` parameter from PEP 695 is not yet
# implemented by mypy.
InferredT = TypeVar("InferredT", infer_variance=True)

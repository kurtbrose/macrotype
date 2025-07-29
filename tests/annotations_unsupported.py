# These annotations use syntax standardized in PEP 695 but unsupported by mypy.
# Each example below includes a comment describing the unsupported feature.

from typing import (
    Callable,
    ClassVar,
    Generic,
    InitVar,
    NewType,
    ParamSpec,
    Concatenate,
    Tuple,
    TypeAlias,
    TypeAliasType,
    TypeVar,
    TypeVarTuple,
    Unpack,
    overload,
    final,
)
from macrotype.meta_types import make_literal_map

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

# ``TypeAliasType`` with type parameters is specified in PEP 695.
# mypy does not yet implement this constructor.
AliasListT = TypeAliasType("AliasListT", list[T], type_params=(T,))
# ``ParamSpec`` alias via TypeAliasType
AliasFuncP = TypeAliasType("AliasFuncP", Callable[P, int], type_params=(P,))
# ``TypeVarTuple`` alias via TypeAliasType
AliasTupleTs = TypeAliasType("AliasTupleTs", tuple[*Ts], type_params=(Ts,))
# Constrained and bound TypeVar aliases via TypeAliasType
AliasNumberLikeList = TypeAliasType(
    "AliasNumberLikeList", list[NumberLike], type_params=(NumberLike,)
)
AliasBoundU = TypeAliasType("AliasBoundU", list[U], type_params=(U,))


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


# Function using ``TypeVarTuple`` which results in PEP 695 syntax
# mypy cannot parse ``def as_tuple[*Ts]`` yet
def as_tuple(*args: Unpack[Ts]) -> Tuple[Unpack[Ts]]:
    return tuple(args)


# Class with ``TypeVarTuple`` parameter list which mypy doesn't support
class Variadic(Generic[*Ts]):
    def __init__(self, *args: Unpack[Ts]) -> None:
        self.args = tuple(args)

    def to_tuple(self) -> Tuple[Unpack[Ts]]:
        return self.args


# Wrapper function using ``Concatenate`` with a ``ParamSpec`` parameter. mypy
# cannot parse the required PEP 695 generic syntax.
def prepend_one(fn: Callable[Concatenate[int, P], int]) -> Callable[P, int]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> int:
        return fn(1, *args, **kwargs)

    return inner


# Dataclass example using ``InitVar`` is rejected by mypy.
@dataclass
class InitVarExample:
    x: int
    init_only: InitVar[int]

    def __post_init__(self, init_only: int) -> None:
        self.x += init_only


# Overloads generated dynamically in a loop are tricky for mypy's resolver.
for typ in (bytes, bytearray):

    @overload
    def loop_over(x: typ) -> str: ...


del typ


def loop_over(x: bytes | bytearray) -> str:
    return str(x)


# Dynamic class built using ``make_literal_map`` introduces overloads and an
# implementation, which mypy refuses in stubs.
EmittedMap = make_literal_map("EmittedMap", {"a": 1, "b": 2})


# Function using ``P.args`` and ``P.kwargs`` requires PEP 695 generics
# which mypy doesn't yet support.
def use_params(*args: P.args, **kwargs: P.kwargs) -> int:
    return 0


# ``TypeVar`` with the ``infer_variance`` parameter from PEP 695 is not yet
# implemented by mypy.
InferredT = TypeVar("InferredT", infer_variance=True)


# ``@final`` decorator on a module-level function is flagged as an error by
# mypy even though it's valid Python.
@final
def final_func(x: int) -> int:
    return x

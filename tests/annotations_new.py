from typing import (
    Any,
    Callable,
    Concatenate,
    Final,
    NewType,
    ParamSpec,
    TypeAlias,
    TypeAliasType,
    TypeVar,
    TypeVarTuple,
    Unpack,
)

from macrotype.meta_types import overload_for

P = ParamSpec("P")

T = TypeVar("T")
Ts = TypeVarTuple("Ts")
U = TypeVar("U", bound=str)
NumberLike = TypeVar("NumberLike", int, float)
CovariantT = TypeVar("CovariantT", covariant=True)
ContravariantT = TypeVar("ContravariantT", contravariant=True)
TDV = TypeVar("TDV")
UserId = NewType("UserId", int)


def with_paramspec_args_kwargs(fn: Callable[P, int], *args: P.args, **kwargs: P.kwargs) -> int: ...


# Wrapper function using ``Concatenate`` with a ``ParamSpec`` parameter
def prepend_one(fn: Callable[Concatenate[int, P], int]) -> Callable[P, int]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> int:
        return fn(1, *args, **kwargs)

    return inner


@overload_for(0)
@overload_for(1)
def special_neg(val: int) -> int:
    match val:
        case 0:
            return 0
        case 1:
            return -1
        case _:
            return -val


@overload_for(val=None)
def parse_int_or_none(val: str | None) -> int | None:
    if val is None:
        return None
    return int(val)


# Type aliases created via ``TypeAliasType``
AliasListT = TypeAliasType("AliasListT", list[T], type_params=(T,))
AliasTupleTs = TypeAliasType("AliasTupleTs", tuple[Unpack[Ts]], type_params=(Ts,))
AliasNumberLikeList = TypeAliasType(
    "AliasNumberLikeList", list[NumberLike], type_params=(NumberLike,)
)
AliasBoundU = TypeAliasType("AliasBoundU", list[U], type_params=(U,))

MyList: TypeAlias = list[int]

# Simple alias to builtin container
Other = dict[str, int]

# Alias using GenericAlias
ListIntGA = list[int]

# Edge case: alias referencing a forward-declared class
ForwardAlias: TypeAlias = "FutureClass"  # noqa: F821

# Type alias for callable using ParamSpec
CallableP: TypeAlias = Callable[P, int]

# PEP 695 ``type`` statements
type StrList = list[str]
type Alias0[T] = list[T]
type Alias1[T] = Alias0[T]
type AliasNewType = UserId
type AliasTypeVar[T] = T
type AliasUnion = int | str
type ListOrSet[T] = list[T] | set[T]
type IntFunc[**P] = Callable[P, int]
type LabeledTuple[*Ts] = tuple[str, *Ts]
type TupleUnpackFirst[*Ts] = tuple[*Ts, int]  # Unpack before trailing element
type RecursiveList[T] = T | list[RecursiveList[T]]


# Basic variable annotations
GLOBAL: int
CONST: Final[str]
# Variable typed ``Any`` to ensure explicit Any is preserved
ANY_VAR: Any
# Variable using ``Callable`` with ellipsis argument list
FUNC_ELLIPSIS: Callable[..., int]
# Unannotated tuple type
TUPLE_UNANN: tuple
# Empty tuple type
TUPLE_EMPTY: tuple[()]
# Single-element tuple type
TUPLE_ONE: tuple[int]
# Variable using tuple ellipsis syntax
TUPLE_VAR: tuple[int, ...]
# Variable using set and frozenset types to test container formatting
SET_VAR: set[int]
FROZENSET_VAR: frozenset[str]


class FutureClass: ...

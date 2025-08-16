# Generated via: macrotype tests/annotations_new.py --modules -o tests/annotations_new.pyi
# Do not edit by hand
# fmt: off
from typing import Any, Callable, Concatenate, Final, Literal, NewType, ParamSpec, TypeVar, TypeVarTuple, Unpack, overload

P = ParamSpec("P")

T = TypeVar("T")

Ts = TypeVarTuple("Ts")

U = TypeVar("U", bound=str)

NumberLike = TypeVar("NumberLike", int, float)

CovariantT = TypeVar("CovariantT", covariant=True)

ContravariantT = TypeVar("ContravariantT", contravariant=True)

TDV = TypeVar("TDV")

UserId = NewType("UserId", int)

def with_paramspec_args_kwargs[**P](fn: Callable[P, int], *args: P.args, **kwargs: P.kwargs) -> int: ...

def prepend_one[**P](fn: Callable[Concatenate[int, P], int]) -> Callable[P, int]: ...

@overload
def special_neg(val: Literal[0]) -> Literal[0]: ...

@overload
def special_neg(val: Literal[1]) -> Literal[-1]: ...

@overload
def special_neg(val: int) -> int: ...

@overload
def parse_int_or_none(val: None) -> None: ...

@overload
def parse_int_or_none(val: None | str) -> None | int: ...

type AliasListT[T] = list[T]

type AliasTupleTs[*Ts] = tuple[Unpack[Ts]]

type AliasNumberLikeList[NumberLike] = list[NumberLike]

type AliasBoundU[U] = list[U]

MyList = list[int]

Other = dict[str, int]

ListIntGA = list[int]

ForwardAlias = FutureClass  # noqa: F821

CallableP = Callable[P, int]

type StrList = list[str]

type Alias0[T] = list[T]

type Alias1[T] = Alias0[T]

type AliasNewType = UserId

type AliasTypeVar[T] = T

type AliasUnion = int | str

type ListOrSet[T] = list[T] | set[T]

type IntFunc[**P] = Callable[P, int]

type LabeledTuple[*Ts] = tuple[str, Unpack[Ts]]

type TupleUnpackFirst[*Ts] = tuple[Unpack[Ts], int]  # Unpack before trailing element

type RecursiveList[T] = T | list[RecursiveList[T]]

class FutureClass:
    ...

GLOBAL: int

CONST: Final[str]

ANY_VAR: Any

FUNC_ELLIPSIS: Callable[..., int]

TUPLE_UNANN: tuple

TUPLE_EMPTY: tuple[()]

TUPLE_ONE: tuple[int]

TUPLE_VAR: tuple[int, ...]

SET_VAR: set[int]

FROZENSET_VAR: frozenset[str]

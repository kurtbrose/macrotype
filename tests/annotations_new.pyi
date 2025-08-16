# Generated via: macrotype tests/annotations_new.py --modules -o tests/annotations_new.pyi
# Do not edit by hand
from typing import (
    Annotated,
    Any,
    Callable,
    Concatenate,
    Final,
    Literal,
    NewType,
    ParamSpec,
    TypeVar,
    TypeVarTuple,
    Unpack,
    overload,
)

P = ParamSpec("P")

T = TypeVar("T")

Ts = TypeVarTuple("Ts")

U = TypeVar("U", bound=str)

NumberLike = TypeVar("NumberLike", int, float)

CovariantT = TypeVar("CovariantT", covariant=True)

ContravariantT = TypeVar("ContravariantT", contravariant=True)

TDV = TypeVar("TDV")

UserId = NewType("UserId", int)

def with_paramspec_args_kwargs[**P](
    fn: Callable[P, int], *args: P.args, **kwargs: P.kwargs
) -> int: ...
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

ANNOTATED_FINAL: Final[int]

ANNOTATED_CLASSVAR: int

LITERAL_STR_VAR: Literal["hi"]

BOX_SIZE: Final[int]

BORDER_SIZE: Final[int]

class FutureClass: ...

UNANNOTATED_CONST: int

UNANNOTATED_STR: str

UNANNOTATED_FLOAT: float

EXPLICIT_NONE: None

NONE_ALIAS: Any

def takes_none_alias(x: None) -> None: ...

class CustomInt(int): ...

UNANNOTATED_CUSTOM_INT: CustomInt

BOOL_TRUE: bool

BOOL_FALSE: bool

SITE_PROV_VAR: int

COMMENTED_VAR: int  # pragma: var

def mult(a, b: int): ...
def takes_optional(x): ...
def takes_none_param(x: None) -> None: ...
def _alias_target() -> None: ...

PRIMARY_ALIAS = _alias_target

SECONDARY_ALIAS = _alias_target

def _wrap(fn): ...
def wrapped_with_default(x: int, y: int) -> int: ...
def commented_func(x: int) -> None: ...  # pragma: func
def UNTYPED_LAMBDA(x, y): ...  # noqa: F821
def TYPED_LAMBDA(a, b): ...

ANNOTATED_EXTRA: str

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

SET_LIST_VAR: set[list[str]]

TUPLE_LIST_VAR: tuple[list[str], int]

CALLABLE_LIST_VAR: list[Callable[[int], str]]

STRICT_UNION: int | str

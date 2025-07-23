from typing import Annotated, Any, Callable, ClassVar, Concatenate, Final, Literal, LiteralString, NamedTuple, Never, NewType, NoReturn, NotRequired, ParamSpec, Protocol, Required, Self, TypeGuard, TypeVar, TypeVarTuple, TypedDict, Unpack, final, overload, override, runtime_checkable
from collections.abc import AsyncIterator, Iterator, Sequence
from dataclasses import dataclass
from enum import Enum, IntEnum
from functools import cached_property
from re import Pattern

T = TypeVar('T')

P = ParamSpec('P')

Ts = TypeVarTuple('Ts')

U = TypeVar('U')

NumberLike = TypeVar('NumberLike')

CovariantT = TypeVar('CovariantT', covariant=True)

ContravariantT = TypeVar('ContravariantT', contravariant=True)

InferredT = TypeVar('InferredT', infer_variance=True)

UserId = NewType('UserId', int)

MyList = list[int]

type StrList = list[str]

type Alias0[T] = list[T]

type Alias1[T] = Alias0[T]

type AliasNewType = UserId

type AliasTypeVar[T] = T

type AliasUnion = int | str

type ListOrSet[T] = list[T] | set[T]

type IntFunc[**P] = Callable[P, int]

type LabeledTuple[*Ts] = tuple[str, Unpack[Ts]]

type RecursiveList[T] = T | list[RecursiveList[T]]

ForwardAlias = FutureClass

type AliasListT[T] = list[T]

type AliasFuncP[**P] = Callable[P, int]

type AliasTupleTs[*Ts] = tuple[Unpack[Ts]]

type AliasNumberLikeList[NumberLike: (int, float)] = list[NumberLike]

type AliasBoundU[U: str] = list[U]

UNTYPED_LAMBDA: function

TYPED_LAMBDA: Callable[[int, int], int]

class Basic:
    simple: list[str]
    mapping: dict[str, int]
    optional: int | None
    union: int | str
    pipe_union: int | str
    func: Callable[[int, str], bool]
    annotated: Annotated[int, 'meta']
    pattern: Pattern[str]
    uid: UserId
    lit_attr: Literal['a', 'b']
    def copy[T](self, param: T) -> T: ...
    def curry[**P](self, f: Callable[P, int]) -> Callable[P, int]: ...
    def literal_method(self, flag: Literal['on', 'off']) -> Literal[1, 0]: ...
    @classmethod
    def cls_method(cls, value: int) -> Basic: ...
    @staticmethod
    def static_method(value: int) -> int: ...
    @property
    def prop(self) -> int: ...
    @cached_property
    def cached(self) -> int: ...
    @property
    def data(self) -> int: ...
    @data.setter
    def data(self, value: int) -> None: ...
    @property
    def temp(self) -> int: ...
    @temp.deleter
    def temp(self) -> None: ...
    class Nested:
        x: float
        y: str

class Child(Basic):
    pass

class OverrideChild(Basic):
    @override
    def copy[T](self, param: T) -> T: ...

class SampleDict(TypedDict):
    name: str
    age: int

class PartialDict(TypedDict, total=False):
    id: int
    hint: str

class MixedDict(TypedDict):
    required_field: int
    optional_field: NotRequired[str]
    required_override: Required[int]

class BaseTD(TypedDict):
    base_field: int

class SubTD(BaseTD):
    sub_field: str

class GenericClass[T]:
    value: T
    def get(self) -> T: ...

class Slotted:
    x: int
    y: str

class HasPartialMethod:
    def base(self, a: int, b: str) -> str: ...
    def pm(self, b: str) -> str: ...

def make_wrapper(t: type): ...

class GeneratedInt:
    value: int

class GeneratedPattern:
    value: Pattern[str]

@overload
def over(x: int) -> int: ...

@overload
def over(x: str) -> str: ...

@dataclass
class Point:
    x: int
    y: int

@dataclass(frozen=True, slots=True)
class Frozen:
    a: int
    b: int

@dataclass(kw_only=True)
class KwOnlyPoint:
    x: int
    y: int

@dataclass(eq=False)
class NoAutoEq:
    x: int
    def __eq__(self, other: object) -> bool: ...

@dataclass(order=True, match_args=False, slots=True, weakref_slot=True)
class OptionDataclass:
    value: int

@dataclass
class InitVarExample:
    x: int
    def __post_init__(self, init_only: int) -> None: ...

@dataclass
class Outer:
    x: int
    @dataclass
    class Inner:
        y: int

@dataclass
class ClassVarExample:
    x: int
    y: ClassVar[int]

class NewGeneric[T]:
    value: T
    def get(self) -> T: ...

class OldGeneric[T]:
    value: T
    def get(self) -> T: ...

class BoundClass[T: int]:
    value: T

class ConstrainedClass[T: (int, str)]:
    value: T

class Color(Enum):
    RED = 1
    GREEN = 2

class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class NamedPoint(NamedTuple):
    x: int
    y: int

def use_tuple(tp: tuple[int, ...]) -> tuple[int, ...]: ...

class SelfExample:
    def clone(self: Self) -> Self: ...

class SelfFactory:
    def __init__(self, value: int) -> None: ...
    @classmethod
    def create(cls: type[Self], value: int) -> Self: ...

@runtime_checkable
class Runnable(Protocol):
    def run(self) -> int: ...

def as_tuple[*Ts](*args: Unpack[Ts]) -> tuple[Unpack[Ts]]: ...

class Variadic[Unpack[Ts]]:
    def __init__(self, *args: Unpack[Ts]) -> None: ...
    def to_tuple(self) -> tuple[Unpack[Ts]]: ...

class Info(TypedDict):
    name: str
    age: int

def with_kwargs(**kwargs: Unpack[Info]) -> Info: ...

def sum_of(*args: tuple[int]) -> int: ...

def dict_echo(**kwargs: dict[str, Any]) -> dict[str, Any]: ...

def prepend_one[**P](fn: Callable[Concatenate[int, P], int]) -> Callable[P, int]: ...

def use_params[**P](*args: P.args, **kwargs: P.kwargs) -> int: ...

def do_nothing() -> None: ...

def always_raises() -> NoReturn: ...

def never_returns() -> Never: ...

def is_str_list(val: list[object]) -> TypeGuard[list[str]]: ...

def echo_literal(value: LiteralString) -> LiteralString: ...

NONE_VAR: None

async def async_add_one(x: int) -> int: ...

async def gen_range(n: int) -> AsyncIterator[int]: ...

@final
def final_func(x: int) -> int: ...

@final
class FinalClass:
    pass

class HasFinalMethod:
    @final
    def do_final(self) -> None: ...

def pos_only_func(a: int, b: str, /) -> None: ...

def kw_only_func(*, x: int, y: str) -> None: ...

def pos_and_kw(a: int, /, b: int, *, c: int) -> None: ...

def iter_sequence(seq: Sequence[int]) -> Iterator[int]: ...

def cached_add(a: int, b: int) -> int: ...

def annotated_fn(x: Annotated[int, 'inp']) -> Annotated[str, 'out']: ...

class FutureClass:
    pass

def _plain_deco(fn: Any): ...

class DecoratedMethods:
    @classmethod
    def cls_decorated(cls, x: int) -> int: ...
    @staticmethod
    def static_decorated(x: int) -> int: ...

GLOBAL: int

CONST: Final[str]

ANY_VAR: Any

FUNC_ELLIPSIS: Callable[..., int]

TUPLE_VAR: tuple[int, ...]

LITERAL_STR_VAR: LiteralString

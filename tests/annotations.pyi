from typing import Any, Callable, ClassVar, Concatenate, Final, Literal, LiteralString, NamedTuple, Never, NewType, NoReturn, NotRequired, ParamSpec, Required, Self, TypeGuard, TypeVar, TypeVarTuple, TypedDict, Unpack, overload
from dataclasses import dataclass
from enum import Enum, IntEnum
from functools import cached_property
from re import Pattern

T = TypeVar('T')

P = ParamSpec('P')

Ts = TypeVarTuple('Ts')

U = TypeVar('U')

NumberLike = TypeVar('NumberLike')

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

type AliasListT[T] = list[T]

type AliasFuncP[**P] = Callable[P, int]

class Basic:
    simple: list[str]
    mapping: dict[str, int]
    optional: int | None
    union: int | str
    pipe_union: int | str
    func: Callable[[int, str], bool]
    annotated: int
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
    class Nested:
        x: float
        y: str

class Child(Basic):
    pass

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

class GenericClass[T]:
    value: T
    def get(self) -> T: ...

class Slotted:
    x: int
    y: str

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

def do_nothing() -> None: ...

def always_raises() -> NoReturn: ...

def never_returns() -> Never: ...

def is_str_list(val: list[object]) -> TypeGuard[list[str]]: ...

def echo_literal(value: LiteralString) -> LiteralString: ...

async def async_add_one(x: int) -> int: ...

GLOBAL: int

CONST: Final[str]

ANY_VAR: Any

FUNC_ELLIPSIS: Callable[..., int]

TUPLE_VAR: tuple[int, ...]

LITERAL_STR_VAR: LiteralString

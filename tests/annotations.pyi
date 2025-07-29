# Generated via: macrotype tests/annotations.py -o -
# Do not edit by hand
from typing import Annotated, Any, Callable, ClassVar, Concatenate, Final, Literal, LiteralString, NamedTuple, Never, NewType, NoReturn, NotRequired, ParamSpec, Protocol, Required, Self, TypeGuard, TypeVar, TypeVarTuple, TypedDict, Unpack, final, overload, override, runtime_checkable
from collections.abc import AsyncIterator, Iterator, Sequence
from dataclasses import InitVar, dataclass
from enum import Enum, IntEnum, IntFlag
from functools import cached_property
from math import sin
from pathlib import Path
from re import Pattern

T = TypeVar('T')

P = ParamSpec('P')

Ts = TypeVarTuple('Ts')

U = TypeVar('U')

NumberLike = TypeVar('NumberLike')

CovariantT = TypeVar('CovariantT', covariant=True)

ContravariantT = TypeVar('ContravariantT', contravariant=True)

TDV = TypeVar('TDV')

UserId = NewType('UserId', int)

type AliasListT[T] = list[T]

type AliasFuncP[**P] = Callable[P, int]

type AliasTupleTs[*Ts] = tuple[Unpack[Ts]]

type AliasNumberLikeList[NumberLike] = list[NumberLike]

type AliasBoundU[U] = list[U]

MyList = list[int]

ForwardAlias = FutureClass

ANNOTATED_FINAL: Final[int]

ANNOTATED_CLASSVAR: int

UNANNOTATED_CONST: int

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
    @classmethod
    def cls_override(cls) -> int: ...
    @staticmethod
    def static_method(value: int) -> int: ...
    @staticmethod
    def static_override() -> int: ...
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

class OverrideLate(Basic):
    @classmethod
    @override
    def cls_override(cls) -> int: ...
    @staticmethod
    @override
    def static_override() -> int: ...

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

class GenericBox[TDV](TypedDict):
    item: TDV

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
    init_only: InitVar[int]
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

class Permission(IntFlag):
    READ = 1
    WRITE = 2
    EXECUTE = 4

class StrEnum(str, Enum):
    A = 'a'
    B = 'b'

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

class Info(TypedDict):
    name: str
    age: int

def with_kwargs(**kwargs: Unpack[Info]) -> Info: ...

def sum_of(*args: tuple[int]) -> int: ...

def dict_echo(**kwargs: dict[str, Any]) -> dict[str, Any]: ...

def do_nothing() -> None: ...

def always_raises() -> NoReturn: ...

def never_returns() -> Never: ...

def is_str_list(val: list[object]) -> TypeGuard[list[str]]: ...

FINAL_VAR_WITH_VALUE: Final[int]

PLAIN_FINAL_VAR: Final[int]

SIN_ALIAS = sin

PI_ALIAS: float

def local_alias_target(x: int) -> int: ...

LOCAL_ALIAS = local_alias_target

def echo_literal(value: LiteralString) -> LiteralString: ...

NONE_VAR: None

async def async_add_one(x: int) -> int: ...

async def gen_range(n: int) -> AsyncIterator[int]: ...

@final
class FinalClass:
    pass

class HasFinalMethod:
    @final
    def do_final(self) -> None: ...

def final_func(x: int) -> int: ...

def pos_only_func(a: int, b: str, /) -> None: ...

def kw_only_func(*, x: int, y: str) -> None: ...

def pos_and_kw(a: int, /, b: int, *, c: int) -> None: ...

def iter_sequence(seq: Sequence[int]) -> Iterator[int]: ...

def simple_wrap(fn: Callable[[int], int]) -> Callable[[int], int]: ...

def double_wrapped(x: int) -> int: ...

def cached_add(a: int, b: int) -> int: ...

def annotated_fn(x: Annotated[int, 'inp']) -> Annotated[str, 'out']: ...

class FutureClass:
    pass

def wrap_descriptor(desc: Any): ...

class WrappedDescriptors:
    @property
    def wrapped_prop(self) -> int: ...
    @classmethod
    def wrapped_cls(cls) -> int: ...
    @staticmethod
    def wrapped_static(x: int) -> int: ...
    @cached_property
    def wrapped_cached(self) -> int: ...

def make_emitter(name: str): ...

def emitted_a(x: int) -> int: ...

def emitted_b(x: int) -> int: ...

def make_emitter_cls(name: str): ...

class EmittedCls:
    value: int

def make_dynamic_cls(): ...

class FixedModuleCls:
    pass

class EmittedMap:
    @overload
    def __getitem__(self, key: Literal['a']) -> Literal[1]: ...
    @overload
    def __getitem__(self, key: Literal['b']) -> Literal[2]: ...

def path_passthrough(p: Path) -> Path: ...

@overload
def loop_over(x: bytearray) -> str: ...

@overload
def loop_over(x: bytes) -> str: ...

def as_tuple[*Ts](*args: Unpack[Ts]) -> tuple[Unpack[Ts]]: ...

class Variadic[*Ts]:
    def __init__(self, *args: Unpack[Ts]) -> None: ...
    def to_tuple(self) -> tuple[Unpack[Ts]]: ...

def prepend_one[**P](fn: Callable[Concatenate[int, P], int]) -> Callable[P, int]: ...

GLOBAL: int

CONST: Final[str]

ANY_VAR: Any

FUNC_ELLIPSIS: Callable[..., int]

TUPLE_VAR: tuple[int, ...]

LITERAL_STR_VAR: LiteralString

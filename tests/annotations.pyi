from typing import Annotated, Any, Callable, ClassVar, Final, Literal, NamedTuple, NewType, NotRequired, ParamSpec, Protocol, Required, Self, TypeVar, TypeVarTuple, TypedDict, Unpack, final, overload, runtime_checkable
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from enum import Enum, IntEnum, IntFlag
from functools import cached_property
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

ANNOTATED_FINAL: Final[int]

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

GLOBAL: int

CONST: Final[str]

ANY_VAR: Any

FUNC_ELLIPSIS: Callable[..., int]

TUPLE_VAR: tuple[int, ...]

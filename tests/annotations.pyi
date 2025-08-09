# Generated via: macrotype tests/annotations.py -o tests/annotations.pyi
# Do not edit by hand
# pyright: basic
from typing import Annotated, Any, Callable, ClassVar, Concatenate, Final, Literal, LiteralString, NamedTuple, Never, NewType, NoReturn, NotRequired, ParamSpec, Protocol, Required, Self, TypeGuard, TypeVar, TypeVarTuple, TypedDict, Unpack, final, overload, override, runtime_checkable
from abc import ABC, abstractmethod
from collections import deque
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

type AliasTupleTs[*Ts] = tuple[Unpack[Ts]]

type AliasNumberLikeList[NumberLike] = list[NumberLike]

type AliasBoundU[U] = list[U]

MyList = list[int]

ForwardAlias = FutureClass

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

ANNOTATED_FINAL: Final[int]

ANNOTATED_CLASSVAR: int

BOX_SIZE: Final[int]

BORDER_SIZE: Final[int]

UNANNOTATED_CONST: int

BOOL_TRUE: bool

BOOL_FALSE: bool

def mult(a, b: int): ...

def takes_optional(x): ...

UNTYPED_LAMBDA: function

TYPED_LAMBDA: Callable[[int, int], int]

ANNOTATED_EXTRA: Annotated[str, 'extra']

NESTED_ANNOTATED: Annotated[int, 'a', 'b']

ANNOTATED_OPTIONAL_META: Annotated[int | None, 'meta']

class UserBox[T]: ...

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

class Child(Basic): ...

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

class Slotted:
    x: int
    y: str

class HasPartialMethod:
    def base(self, a: int, b: str) -> str: ...
    def pm(self, b: str) -> str: ...

def make_wrapper(t: type): ...

class GeneratedInt:
    value: int

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

class NewGeneric[T]:
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

class VarNamedTuple[*Ts](NamedTuple):
    items: tuple[Unpack[Ts]]

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

def sum_of(*args: tuple[int, ...]) -> int: ...

def dict_echo(**kwargs: dict[str, Any]) -> dict[str, Any]: ...

def use_params[**P](func: Callable[P, int], *args: P.args, **kwargs: P.kwargs) -> int: ...

def do_nothing() -> None: ...

def always_raises() -> NoReturn: ...

def never_returns() -> Never: ...

def is_str_list(val: list[object]) -> TypeGuard[list[str]]: ...

def is_int(val: object) -> TypeGuard[int]: ...

PLAIN_FINAL_VAR: Final[int]

SIN_ALIAS = sin

PI_ALIAS: float

PRAGMA_VAR: int  # type: ignore

def local_alias_target(x: int) -> int: ...

LOCAL_ALIAS = local_alias_target

def echo_literal(value: LiteralString) -> LiteralString: ...

NONE_VAR: None

async def async_add_one(x: int) -> int: ...

async def gen_range(n: int) -> AsyncIterator[int]: ...

@final
class FinalClass: ...

class HasFinalMethod:
    @final
    def do_final(self) -> None: ...

def final_func(x: int) -> int: ...

def pragma_func(x: int) -> int: ...  # pyright: ignore

def pos_only_func(a: int, b: str, /) -> None: ...

def kw_only_func(*, x: int, y: str) -> None: ...

def pos_and_kw(a: int, /, b: int, *, c: int) -> None: ...

def iter_sequence(seq: Sequence[int]) -> Iterator[int]: ...

def simple_wrap(fn: Callable[[int], int]) -> Callable[[int], int]: ...

def double_wrapped(x: int) -> int: ...

def cached_add(a: int, b: int) -> int: ...

def annotated_fn(x: Annotated[int, 'inp']) -> Annotated[str, 'out']: ...

class FutureClass: ...

def wrap_descriptor(desc): ...

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

def make_emitter_cls(name: str): ...

class EmittedCls:
    value: int

def make_dynamic_cls(): ...

class FixedModuleCls: ...

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

@overload
def special_neg(val: Literal[0]) -> Literal[0]: ...

@overload
def special_neg(val: Literal[1]) -> Literal[-1]: ...

@overload
def special_neg(val: int) -> int: ...

@overload
def parse_int_or_none(val: None) -> None: ...

@overload
def parse_int_or_none(val: str | None) -> int | None: ...

@overload
def times_two(val: Literal[3], factor: Literal[2]) -> Literal[6]: ...

@overload
def times_two(val: int, factor: int) -> int: ...

@overload
def bool_gate(flag: Literal[True]) -> Literal[1]: ...

@overload
def bool_gate(flag: Literal[False]) -> Literal[0]: ...

@overload
def bool_gate(flag: bool) -> int: ...

class AbstractBase(ABC):
    @abstractmethod
    def do_something(self) -> int: ...

class BadParams:
    value: int

class Mapped[T]: ...

class SQLBase:
    @classmethod
    def __init_subclass__(cls) -> None: ...

ManagerModelId = NewType('ManagerModelId', int)

class ManagerModel(SQLBase):
    id: Mapped[ManagerModelId]
    id_type: type[ManagerModelId]

EmployeeModelId = NewType('EmployeeModelId', int)

class EmployeeModel(SQLBase):
    manager_id: Mapped[ManagerModelId]
    id: Mapped[EmployeeModelId]
    id_type: type[EmployeeModelId]

def strip_null(ann: Any, null: Any) -> Any: ...

class Cls:
    a: int
    b: float | None
    c: str | None
    d: bytes

class OptionalCls:
    a: int | None
    b: float | None
    c: str | None
    d: bytes | None

class RequiredCls:
    a: int
    b: float
    c: str
    d: bytes

class PickedCls:
    a: int
    b: float | None

class OmittedCls:
    a: int
    b: float | None

class FinalCls:
    a: Final[int]
    b: Final[float | None]
    c: Final[str | None]
    d: Final[bytes]

class ReplacedCls:
    a: str
    b: bool
    c: str | None
    d: bytes

class BaseInherit:
    base: int

class SubInherit(BaseInherit):
    sub: str

class InheritedOmit:
    base: int

class InheritedFinal:
    base: Final[int]
    sub: Final[str]

class Undefined: ...

class UndefinedCls:
    a: int
    b: str | Undefined

class OptionalUndefinedCls:
    a: int | Undefined
    b: str | Undefined

class RequiredUndefinedCls:
    a: int
    b: str

GLOBAL: int

CONST: Final[str]

ANY_VAR: Any

FUNC_ELLIPSIS: Callable[..., int]

TUPLE_VAR: tuple[int, ...]

SET_VAR: set[int]

FROZENSET_VAR: frozenset[str]

GENERIC_DEQUE: deque[int]

GENERIC_USERBOX: UserBox[int]

LITERAL_STR_VAR: LiteralString

DICT_WITH_IMPLICIT_ANY: dict[int]  # type: ignore[type-arg]  # pyright: ignore[reportInvalidTypeArguments]

UNPARAM_LIST: list

LIST_INT_ONLY: list[int]

LIST_INT_OR_STR: list[int | str]

LIST_NESTED_UNION: list[int | None | str]

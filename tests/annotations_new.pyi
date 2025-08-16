# Generated via: macrotype tests/annotations_new.py --modules -o tests/annotations_new.pyi
# Do not edit by hand
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import AsyncIterator, Iterator, Sequence
from dataclasses import InitVar, dataclass
from enum import Enum, IntEnum, IntFlag
from functools import cached_property
from math import sin
from pathlib import Path
from re import Pattern
from typing import (
    Annotated,
    Any,
    Callable,
    ClassVar,
    Concatenate,
    Final,
    Literal,
    LiteralString,
    Never,
    NewType,
    NotRequired,
    ParamSpec,
    Protocol,
    Required,
    Self,
    TypedDict,
    TypeGuard,
    TypeVar,
    TypeVarTuple,
    Unpack,
    final,
    overload,
    override,
    runtime_checkable,
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

def pos_only_func(a: int, b: str) -> None: ...
def kw_only_func(x: int, y: str) -> None: ...
def pos_and_kw(a: int, b: int, c: int) -> None: ...
def iter_sequence(seq: Sequence[int]) -> Iterator[int]: ...
def simple_wrap(fn: Callable[[int], int]) -> Callable[[int], int]: ...
def double_wrapped(x: int) -> int: ...
def cached_add(a: int, b: int) -> int: ...
def annotated_fn(x: Annotated[int, "inp"]) -> Annotated[str, "out"]: ...
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
    def __getitem__(self, key: Literal["a"]) -> Literal[1]: ...
    @overload
    def __getitem__(self, key: Literal["b"]) -> Literal[2]: ...

def path_passthrough(p: Path) -> Path: ...
@overload
def loop_over(x: bytearray) -> str: ...
@overload
def loop_over(x: bytes) -> str: ...
def identity[T](x: T) -> T: ...
def as_tuple[*Ts](*args: Unpack[Ts]) -> tuple[Unpack[Ts]]: ...

class Variadic[*Ts]:
    def __init__(self, *args: Unpack[Ts]) -> None: ...
    def to_tuple(self) -> tuple[Unpack[Ts]]: ...

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
@overload
def mixed_overload(x: str) -> str: ...
@overload
def mixed_overload(x: Literal[0]) -> Literal[0]: ...
@overload
def mixed_overload(x: int | str) -> int | str: ...

class AbstractBase(ABC):
    @abstractmethod
    def do_something(self) -> int: ...

class BadParams:
    value: int

class Mapped[T]: ...

class SQLBase:
    @classmethod
    def __init_subclass__(cls) -> None: ...

ManagerModelId = NewType("ManagerModelId", int)

class ManagerModel(SQLBase):
    id: Mapped[ManagerModelId]
    id_type = NewType("id_type", int)

EmployeeModelId = NewType("EmployeeModelId", int)

class EmployeeModel(SQLBase):
    manager_id: Mapped[ManagerModelId]
    id: Mapped[EmployeeModelId]
    id_type = NewType("id_type", int)

def sum_of(*args: tuple[int]) -> int: ...
def dict_echo(**kwargs: dict[str, Any]) -> dict[str, Any]: ...
def use_params[**P](func: Callable[P, int], *args: P.args, **kwargs: P.kwargs) -> int: ...
def is_str_list(val: list[object]) -> TypeGuard[list[str]]: ...
def is_int(val: object) -> TypeGuard[int]: ...

PLAIN_FINAL_VAR: Final[int]

SIN_ALIAS = sin

COS_VAR: Callable[[float], float]

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
def do_nothing() -> None: ...
def always_raises() -> Never: ...
def never_returns() -> Never: ...

class SelfExample:
    def clone(self: Self) -> Self: ...

class SelfFactory:
    def __init__(self, value: int) -> None: ...
    @classmethod
    def create(cls: type[Self], value: int) -> Self: ...

@runtime_checkable
class Runnable(Protocol):
    def run(self) -> int: ...

@runtime_checkable
class LaterRunnable(Protocol):
    def run(self) -> int: ...

class NoProtoMethods(Protocol): ...

class Info(TypedDict):
    name: str
    age: int

def with_kwargs(**kwargs: Unpack[Info]) -> Info: ...

class ManualProperty:
    @property
    def both(self) -> int: ...
    @both.setter
    def both(self, value: int) -> None: ...
    @both.deleter
    def both(self) -> None: ...

class SampleDict(TypedDict):
    name: str
    age: int

class PartialDict(TypedDict):
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

class TDShadowBase(TypedDict):
    base_only: int
    shadow: str

class TDShadowChild(TDShadowBase):
    extra: float

class GenericBox[TDV](TypedDict):
    item: TDV

class Slotted:
    x: int
    y: str

class HasPartialMethod:
    def base(self, a: int, b: str) -> str: ...
    def pm(self, b: str) -> str: ...

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
    init_list: InitVar[list[int]]
    def __post_init__(self, init_only: int, init_list: list[int]) -> None: ...

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

class ClassVarListExample:
    items: ClassVar[list[int]]

class OldGeneric[T]:
    value: T
    def get(self) -> T: ...

class NewGeneric[T]:
    value: T
    def get(self) -> T: ...

class BoundClass[T]:
    value: T

class ConstrainedClass[T]:
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
    A = "a"
    B = "b"

class PointEnum(Enum):
    INLINE = Point
    REF = Point

def use_tuple(tp: tuple[int, ...]) -> tuple[int, ...]: ...

class UserBox[T]: ...

NESTED_ANNOTATED: Annotated[int, "a", "b"]

TRIPLE_ANNOTATED: Annotated[int, "x", "y", "z"]

ANNOTATED_OPTIONAL_META: Annotated[int | None, "meta"]

ANNOTATED_FINAL_META: Final[Annotated[int, "meta"]]

ANNOTATED_WRAP_GENERIC: Annotated[list[Annotated[int, "inner"]], "outer"]

class MetaRepr:
    def __repr__(self) -> str: ...  # pragma: no cover - simple repr

ANNOTATED_OBJ_META: Annotated[int, MetaRepr()]

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

ForwardAlias = "FutureClass"  # noqa: F821

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

LITERAL_STR_QUOTED: Literal["hi"]

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

ANNOTATED_EXTRA: Annotated[str, "extra"]

class Basic:
    simple: list[str]
    mapping: dict[str, int]
    optional: None | int
    union: int | str  # typing.Union should remain unaltered
    pipe_union: int | str
    func: Callable[[int, str], bool]
    annotated: Annotated[int, "meta"]
    pattern: Pattern[str]
    uid: UserId
    lit_attr: Literal["a", "b"]
    def copy[T](self, param: T) -> T: ...
    def curry[**P](self, f: Callable[P, int]) -> Callable[P, int]: ...
    def literal_method(self, flag: Literal["on", "off"]) -> Literal[1, 0]: ...
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

    @cached_property
    def cached(self) -> int: ...

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

LITERAL_STR_VAR: LiteralString

DICT_WITH_IMPLICIT_ANY: dict[int]  # type: ignore[type-arg]  # pyright: ignore[reportInvalidTypeArguments]

DICT_LIST_VALUE: dict[str, list[int]]

UNPARAM_LIST: list

GENERIC_DEQUE: deque[int]

GENERIC_DEQUE_LIST: deque[list[str]]

GENERIC_USERBOX: UserBox[int]

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

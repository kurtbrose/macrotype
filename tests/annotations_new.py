import collections.abc as cabc
import functools
import math
import re
import sys
import types
import typing
from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass
from enum import Enum, IntEnum, IntFlag
from functools import cached_property
from operator import attrgetter
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Callable,
    ClassVar,
    Concatenate,
    Deque,
    Final,
    Generic,
    Literal,
    LiteralString,
    NamedTuple,
    Never,
    NewType,
    NotRequired,
    Optional,
    ParamSpec,
    Protocol,
    Required,
    Self,
    TypeAlias,
    TypeAliasType,
    TypedDict,
    TypeGuard,
    TypeVar,
    TypeVarTuple,
    Union,
    Unpack,
    final,
    override,
    runtime_checkable,
)

from sqlalchemy.engine import Result as SAResult
from sqlalchemy.sql.selectable import (
    AliasedReturnsRows as SAAliasedReturnsRows,
)
from sqlalchemy.sql.selectable import (
    ExecutableReturnsRows as SAExecutableReturnsRows,
)
from sqlalchemy.sql.selectable import (
    ReturnsRows as SAReturnsRows,
)
from sqlalchemy.sql.selectable import (
    Select as SASelect,
)
from sqlalchemy.sql.selectable import (
    TypedReturnsRows as SATypedReturnsRows,
)

import macrotype.meta_types as mt
from macrotype.meta_types import (
    emit_as,
    get_caller_module,
    make_literal_map,
    overload,
    overload_for,
    set_module,
)
from tests.external_nested import ExternalOuter

# Imported assignment should remain a simple import in stubs
from tests.modules.namespace_assign import namespace  # noqa: F401

# Imported proxy raising on __name__ access to ensure safe getattr
from tests.modules.proxy_module import PROXY as IMPORTED_PROXY  # noqa: F401

P = ParamSpec("P")

T = TypeVar("T")
Ts = TypeVarTuple("Ts")
U = TypeVar("U", bound=str)
NumberLike = TypeVar("NumberLike", int, float)
CovariantT = TypeVar("CovariantT", covariant=True)
ContravariantT = TypeVar("ContravariantT", contravariant=True)
TDV = TypeVar("TDV")
UserId = NewType("UserId", int)


# Object that raises from __getattr__ for specific attributes to ensure safe
# attribute access
class RaisingProxy:
    def __getattr__(self, name: str) -> typing.Any:
        if name in {"__module__", "__supertype__"}:
            raise RuntimeError("boom")
        raise AttributeError(name)

    def __call__(self) -> None:
        pass


RAISING_PROXY = RaisingProxy()

# TypeScript-inspired metaclass utilities


def strip_null(ann: Any, null: Any) -> Any:
    origin = typing.get_origin(ann)
    if origin in {typing.Union, types.UnionType}:
        args = [a for a in typing.get_args(ann) if a is not null]
        if not args:
            return null
        result = args[0]
        for a in args[1:]:
            result |= a
        return result
    return ann


class Cls:
    a: int
    b: float | None
    c: str | None
    d: bytes


class OptionalCls:
    __annotations__ = {k: v | None for k, v in mt.all_annotations(Cls).items()}


class RequiredCls:
    __annotations__ = {k: strip_null(v, type(None)) for k, v in mt.all_annotations(Cls).items()}


class PickedCls:
    __annotations__ = {k: v for k, v in mt.all_annotations(Cls).items() if k in {"a", "b"}}


class OmittedCls:
    __annotations__ = {k: v for k, v in mt.all_annotations(Cls).items() if k not in {"c", "d"}}


class FinalCls:
    __annotations__ = {k: Final[v] for k, v in mt.all_annotations(Cls).items()}


ReplacedCls = type(
    "ReplacedCls",
    (),
    {"__annotations__": {**mt.all_annotations(Cls), "a": str, "b": bool}},
)


class BaseInherit:
    base: int


class SubInherit(BaseInherit):
    sub: str


class InheritedOmit:
    __annotations__ = {k: v for k, v in mt.all_annotations(SubInherit).items() if k != "sub"}


class InheritedFinal:
    __annotations__ = {k: Final[v] for k, v in mt.all_annotations(SubInherit).items()}


# optional() and required() with a custom null sentinel
class Undefined: ...


class UndefinedCls:
    a: int
    b: str | Undefined


class OptionalUndefinedCls:
    __annotations__ = {k: v | Undefined for k, v in mt.all_annotations(UndefinedCls).items()}


class RequiredUndefinedCls:
    __annotations__ = {
        k: strip_null(v, Undefined) for k, v in mt.all_annotations(UndefinedCls).items()
    }


# Edge case: LiteralString handling
LITERAL_STR_VAR: LiteralString
# Dict without explicit value type should remain as written
DICT_WITH_IMPLICIT_ANY: dict[int]  # type: ignore[type-arg]  # pyright: ignore[reportInvalidTypeArguments]
# Dict with nested list to exercise TypeNode in dict key/value
DICT_LIST_VALUE: dict[str, list[int]]
# Generic container without type arguments should remain unparameterized
UNPARAM_LIST: list


# Edge case: positional-only and keyword-only parameters
def pos_only_func(a: int, b: str, /) -> None:
    pass


def kw_only_func(*, x: int, y: str) -> None:
    pass


def pos_and_kw(a: int, /, b: int, *, c: int) -> None:
    pass


# Edge case: using ``collections.abc`` generic types
def iter_sequence(seq: cabc.Sequence[int]) -> cabc.Iterator[int]:
    for item in seq:
        yield item


# Edge case: decorated functions should retain original signature
def simple_wrap(fn: Callable[[int], int]) -> Callable[[int], int]:
    @functools.wraps(fn)
    def inner(x: int) -> int:
        return fn(x)

    return inner


@simple_wrap
@simple_wrap
def double_wrapped(x: int) -> int:
    return x + 1


@functools.lru_cache()
def cached_add(a: int, b: int) -> int:
    return a + b


# Edge case: ``Annotated`` parameter and return types
def annotated_fn(x: Annotated[int, "inp"]) -> Annotated[str, "out"]:
    return str(x)


# Helper decorator to wrap descriptors and set ``__wrapped__``
def wrap_descriptor(desc):
    class Wrapper:
        def __init__(self, d):
            self.__wrapped__ = d
            self._d = d

        def __get__(self, obj, objtype=None):
            return self._d.__get__(obj, objtype)

        def __set__(self, obj, value):
            return self._d.__set__(obj, value)

        def __delete__(self, obj):
            return self._d.__delete__(obj)

    return Wrapper(desc)


class WrappedDescriptors:
    """Class with descriptors wrapped by another decorator."""

    @wrap_descriptor
    @property
    def wrapped_prop(self) -> int:
        return 1

    @wrap_descriptor
    @classmethod
    def wrapped_cls(cls) -> int:
        return 2

    @wrap_descriptor
    @staticmethod
    def wrapped_static(x: int) -> int:
        return x

    @wrap_descriptor
    @cached_property
    def wrapped_cached(self) -> int:
        return 3


# Test emit_as decorator for functions
def make_emitter(name: str):
    @emit_as(name)
    def inner(x: int) -> int:
        return x

    return inner


emitted_a = make_emitter("emitted_a")


# Test emit_as decorator for classes
def make_emitter_cls(name: str):
    @emit_as(name)
    class Inner:
        value: int

    return Inner


EmittedCls = make_emitter_cls("EmittedCls")


# Use emit_as with overloads defined dynamically on a class via API helper


# Demonstrate adjusting a dynamically created class using helpers
def make_dynamic_cls():
    cls = type("FixedModuleCls", (), {"__module__": "tests.factory"})
    set_module(cls, get_caller_module())
    return cls


FixedModuleCls = make_dynamic_cls()

# Dynamic class built using ``make_literal_map`` for typed lookup
EmittedMap = make_literal_map("EmittedMap", {"a": 1, "b": 2})


# Used to verify import path canonicalization across Python versions
def path_passthrough(p: Path) -> Path:
    return p


for typ in (bytearray, bytes):

    @overload
    def loop_over(x: typ) -> str: ...


del typ


def loop_over(x: bytes | bytearray) -> str:
    return str(x)


# Basic generic function using ``TypeVar``
def identity(x: T) -> T:
    return x


# Generic function using ``TypeVarTuple``
def as_tuple(*args: Unpack[Ts]) -> tuple[Unpack[Ts]]:
    return tuple(args)


# Class with variadic type parameters
class Variadic(Generic[*Ts]):
    def __init__(self, *args: Unpack[Ts]) -> None:
        self.args = tuple(args)

    def to_tuple(self) -> tuple[Unpack[Ts]]:
        return self.args


# Overloaded function with PEP 695 type parameters
class Wrapped(Generic[T]):
    pass


@overload
def pep695_overload[T](x: Wrapped[tuple[T]]) -> T: ...


@overload
def pep695_overload[T, T2, *Ts](x: Wrapped[tuple[T, T2, *Ts]]) -> tuple[T, T2, *Ts]: ...


def pep695_overload(x):
    return x


# Default argument example to ensure defaults are applied in overloads
@overload_for(3)
def times_two(val: int, factor: int = 2) -> int:
    return val * factor


# Edge case: overload_for should support boolean literals
@overload_for(True)
@overload_for(False)
def bool_gate(flag: bool) -> int:
    return 1 if flag else 0


# Edge case: ``overload_for`` should handle NaN without Literal[nan]
@overload_for(math.nan)
def nan_case(x: float | str) -> float:
    if isinstance(x, float):
        return x
    return float("nan")


# Edge case: ``overload_for`` should handle float values without Literal
@overload_for(1.5)
def float_case(x: float | str) -> float:
    if isinstance(x, float):
        return x
    return float(x)


# Edge case: ``overload_for`` should handle bytes values
@overload_for(b"x")
def bytes_case(x: bytes) -> bytes:
    return x


# Mixing standard overloads with ``overload_for`` literal cases
@overload
def mixed_overload(x: str) -> str: ...


@overload_for(0)
def mixed_overload(x: int | str) -> int | str:
    if x == 0:
        return 0
    if isinstance(x, str):
        return x
    return x


# Class with an abstract method to verify abstract decorators
class AbstractBase(ABC):
    @abstractmethod
    def do_something(self) -> int: ...


# Class with non-iterable __parameters__ to ensure graceful handling
class BadParams:
    __parameters__ = 1
    value: int


# Demo: dynamically generate a NewType per subclass
class Mapped(Generic[T]): ...


class SQLBase:
    def __init_subclass__(cls) -> None:
        typename = f"{cls.__name__}Id"
        new_type = NewType(typename, int)
        cls.id_type = new_type
        cls.__annotations__["id"] = Mapped[new_type]
        cls.__annotations__["id_type"] = type[new_type]
        sys.modules[cls.__module__].__dict__[typename] = new_type


class ManagerModel(SQLBase): ...


class EmployeeModel(SQLBase):
    manager_id: Mapped[ManagerModel.id_type]


# Forward reference to a local class should not generate typing imports
class ForwardRefModel: ...


class UsesForwardRef:
    items: list["ForwardRefModel"]


# Basic callable examples
def sum_of(*args: tuple[int]) -> int:
    return sum(args)


def dict_echo(**kwargs: dict[str, Any]) -> dict[str, Any]:
    return kwargs


# Edge case: direct use of ``P.args`` and ``P.kwargs``
def use_params(func: Callable[P, int], *args: P.args, **kwargs: P.kwargs) -> int:
    return func(*args, **kwargs)


# Edge case: ``TypeGuard`` return type
def is_str_list(val: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(v, str) for v in val)


# Additional TypeGuard example
def is_int(val: object) -> TypeGuard[int]:
    return isinstance(val, int)


# Edge case: ``Final`` annotated variable with a value
PLAIN_FINAL_VAR: Final[int] = 1


# Edge case: alias to a foreign function should be preserved
SIN_ALIAS = math.sin


# Foreign function with annotation should stay a variable
COS_VAR: Callable[[float], float] = math.cos


# Edge case: alias to a foreign constant should retain its type
PI_ALIAS = math.pi


# Alias to a built-in classmethod implemented in C
DICT_FROMKEYS_CM = dict.fromkeys


# operator.attrgetter returns a callable without __name__
ATTRGETTER_VAR = attrgetter("b")

# operator.attrgetter instance used as Annotated metadata
ANNOTATED_ATTRGETTER_META: Annotated[int, attrgetter("c")] = 0

# Variable with pragma comment should retain comment in stub
PRAGMA_VAR = 1  # type: ignore


def local_alias_target(x: int) -> int:
    return x


# Edge case: alias to a local function should be preserved
LOCAL_ALIAS = local_alias_target


def echo_literal(value: LiteralString) -> LiteralString:
    return value


# Edge case: variable annotated as ``None``
NONE_VAR: None = None


# Edge case: async function
async def async_add_one(x: int) -> int:
    return x + 1


# Edge case: async generator function
async def gen_range(n: int) -> cabc.AsyncIterator[int]:
    for i in range(n):
        yield i


# Edge case: ``final`` decorator handling
@final
class FinalClass: ...


class HasFinalMethod:
    @final
    def do_final(self) -> None:
        pass


@final
def final_func(x: int) -> int:
    return x


# Function with pragma comment should retain comment in stub
def pragma_func(x: int) -> int:  # pyright: ignore
    return x


# Edge case: function explicitly returning ``None``
def do_nothing() -> None:
    return None


# Functions with special control flow
def always_raises() -> Never:
    raise RuntimeError()


def never_returns() -> Never:
    raise RuntimeError()


# Self and runtime checkable protocol examples
class SelfExample:
    def clone(self: Self) -> Self:
        return self


class SelfFactory:
    def __init__(self, value: int) -> None:
        self.value = value

    @classmethod
    def create(cls: type[Self], value: int) -> Self:
        return cls(value)


@runtime_checkable
class Runnable(Protocol):
    def run(self) -> int: ...


# runtime_checkable applied after class definition should be preserved
class LaterRunnable(Protocol):
    def run(self) -> int: ...


LaterRunnable = runtime_checkable(LaterRunnable)


# Protocol auto methods should be pruned
class NoProtoMethods(Protocol):
    pass


class Info(TypedDict):
    name: str
    age: int


def with_kwargs(**kwargs: Unpack[Info]) -> Info:
    return kwargs


# Property with both setter and deleter
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


class PartialDict(TypedDict, total=False):
    id: int
    hint: str


class MixedDict(TypedDict):
    required_field: int
    optional_field: NotRequired[str]
    required_override: Required[int]


# Edge case: TypedDict inheritance should retain base class
class BaseTD(TypedDict):
    base_field: int


class SubTD(BaseTD):
    sub_field: str


# Edge case: TypedDict field shadowing should be pruned
class TDShadowBase(TypedDict):
    base_only: int
    shadow: str


class TDShadowChild(TDShadowBase):
    shadow: str
    extra: float


# Edge case: Generic TypedDict should retain type parameters
class GenericBox(TypedDict, Generic[TDV]):
    item: TDV


class Slotted:
    __slots__ = ("x", "y")
    x: int
    y: str


# Edge case: ``functools.partialmethod`` should generate a normal method stub
class HasPartialMethod:
    def base(self, a: int, b: str) -> str:
        return b * a

    pm = functools.partialmethod(base, 2)


@overload
def over(x: int) -> int: ...


@overload
def over(x: str) -> str: ...


def over(x: int | str) -> int | str:
    return x


@dataclass
class Point:
    x: int
    y: int


@dataclass(frozen=True, slots=True)
class Frozen:
    a: int
    b: int


# Dataclass using ``kw_only=True``
@dataclass(kw_only=True)
class KwOnlyPoint:
    x: int
    y: int


# Dataclass using ``eq=False`` ensures explicit ``__eq__`` is retained
@dataclass(eq=False)
class NoAutoEq:
    x: int

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NoAutoEq) and self.x == other.x


# Dataclass with additional options to test decorator generation
# ``weakref_slot=True`` requires ``slots=True``
@dataclass(order=True, match_args=False, slots=True, weakref_slot=True)
class OptionDataclass:
    value: int


# Edge case: dataclasses.InitVar fields should not appear in stubs
@dataclass
class InitVarExample:
    x: int
    init_only: InitVar[int]
    init_list: InitVar[list[int]]

    def __post_init__(self, init_only: int, init_list: list[int]) -> None:
        self.x += init_only + len(init_list)


@dataclass
class Outer:
    x: int

    @dataclass
    class Inner:
        y: int


@dataclass
class ClassVarExample:
    x: int
    y: ClassVar[int] = 0


# ClassVar wrapping a container type to ensure inner TypeNode handling
class ClassVarListExample:
    items: ClassVar[list[int]] = []


class OldGeneric(Generic[T]):
    value: T

    def get(self) -> T:
        return self.value


# PEP 695 generic class syntax
class NewGeneric[T]:
    value: T

    def get(self) -> T:
        return self.value


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


# Edge case: IntFlag shouldn't expose autogenerated bitwise methods
class Permission(IntFlag):
    READ = 1
    WRITE = 2
    EXECUTE = 4


# Edge case: Enum subclassing ``str`` shouldn't expose autogenerated dunder methods
class StrEnum(str, Enum):
    A = "a"
    B = "b"


ORIGIN = Point(x=0, y=0)


# Enum with custom value types to ensure constructor and variable names are emitted
class PointEnum(Enum):
    INLINE = Point(x=1, y=2)
    REF = ORIGIN


def use_tuple(tp: tuple[int, ...]) -> tuple[int, ...]:
    return tp


GENERIC_DEQUE: Deque[int]
# Deque with nested list to exercise TypeNode inside GenericNode
GENERIC_DEQUE_LIST: Deque[list[str]]


# User-defined generic class to exercise GenericNode
class UserBox(Generic[T]):
    pass


GENERIC_USERBOX: UserBox[int]


# Nested Annotated usage should merge metadata
NESTED_ANNOTATED: Annotated[Annotated[int, "a"], "b"] = 3
# Triple-nested Annotated should preserve structure
TRIPLE_ANNOTATED: Annotated[Annotated[Annotated[int, "x"], "y"], "z"] = 4
# Annotated union to ensure metadata is preserved with unions
ANNOTATED_OPTIONAL_META: Annotated[int | None, "meta"] = 0
# Annotated combined with Final wrapper to verify root handling
ANNOTATED_FINAL_META: Annotated[Final[int], "meta"] = 2
# Outer Annotated around a generic with inner Annotated element
ANNOTATED_WRAP_GENERIC: Annotated[list[Annotated[int, "inner"]], "outer"] = []


# Annotated metadata using arbitrary object to verify pass-through
class MetaRepr:
    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return "MetaRepr()"


META_REPR = MetaRepr()
ANNOTATED_OBJ_META: Annotated[int, META_REPR] = 0


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
# Set containing a nested list to exercise TypeNode in set elements
SET_LIST_VAR: set[list[str]]
# Tuple containing a nested list to exercise TypeNode in tuple items
TUPLE_LIST_VAR: tuple[list[str], int]
# List containing a callable to exercise TypeNode in callable parts
CALLABLE_LIST_VAR: list[Callable[[int], str]]
# Edge case: annotated constants with values should honor the annotation
ANNOTATED_FINAL: Final[int] = 5
ANNOTATED_CLASSVAR: int = 1

# Literal string should retain quotes
LITERAL_STR_QUOTED: Literal["hi"] = "hi"

# ``Final`` without explicit type should infer from value
BOX_SIZE: Final = 20
BORDER_SIZE: Final = 4


class FutureClass: ...


# Edge case: unannotated constant should be included
UNANNOTATED_CONST = 42
# Edge case: unannotated string constant should be included
UNANNOTATED_STR = "hi"
# Edge case: unannotated float constant should be included
UNANNOTATED_FLOAT = 1.23
# Edge case: unannotated complex constant should be included
UNANNOTATED_COMPLEX = 1 + 2j
# Explicit None annotation should remain None
EXPLICIT_NONE: None = None


# Aliasing None shouldn't affect annotation rendering
NONE_ALIAS = None


def takes_none_alias(x: NONE_ALIAS) -> NONE_ALIAS:
    pass


# Edge case: subclass constants should preserve subclass type
class CustomInt(int):
    pass


UNANNOTATED_CUSTOM_INT = CustomInt(7)

# Edge case: boolean constants should be retained
BOOL_TRUE = True
BOOL_FALSE = False

# Variable to test Site provenance handling
SITE_PROV_VAR: int = 1

# Union variable used to exercise strict normalization
STRICT_UNION: Union[str, int]


COMMENTED_VAR: int = 1  # pragma: var


# Unannotated parameters infer type from default values
def mult(a, b=1):
    return a * b


# Defaults of ``None`` do not refine "Any"
def takes_optional(x=None):
    return x


# Explicit None parameter annotation should emit None, not NoneType
def takes_none_param(x: None) -> None:
    pass


# Duplicate local aliases should be canonicalized
def _alias_target() -> None: ...


PRIMARY_ALIAS = _alias_target
SECONDARY_ALIAS = _alias_target


# Decorated function should be unwrapped and defaults inferred
def _wrap(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        return fn(*args, **kwargs)

    return inner


@_wrap
def wrapped_with_default(x: int, y=1) -> int:
    return x + y


def commented_func(x: int) -> None:  # pragma: func
    pass


# Edge case: lambda expressions should be treated as variables, not functions
UNTYPED_LAMBDA = lambda x, y: x + y  # noqa: F821
TYPED_LAMBDA: Callable[[int, int], int] = lambda a, b: a + b

# Additional variable using ``Annotated`` to test type parsing
ANNOTATED_EXTRA: Annotated[str, "extra"] = "x"


class Basic:
    simple: list[str]
    mapping: dict[str, int]
    optional: Optional[int]
    union: Union[int, str]  # typing.Union should remain unaltered
    pipe_union: int | str
    func: Callable[[int, str], bool]
    annotated: Annotated[int, "meta"]
    pattern: re.Pattern[str]
    uid: UserId
    lit_attr: Literal["a", "b"]

    def copy(self, param: T) -> T: ...

    def curry(self, f: Callable[P, int]) -> Callable[P, int]: ...

    def literal_method(self, flag: Literal["on", "off"]) -> Literal[1, 0]: ...

    @classmethod
    def cls_method(cls, value: int) -> "Basic": ...

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


# Edge case: ``@override`` decorator handling
class OverrideChild(Basic):
    @override
    def copy(self, param: T) -> T:
        return param


# Edge case: @override applied after descriptor
class OverrideLate(Basic):
    @override
    @classmethod
    def cls_override(cls) -> int:
        return 1

    @override
    @staticmethod
    def static_override() -> int:
        return 2


# Edge case: @override applied before descriptor
class OverrideEarly(Basic):
    @classmethod
    @override
    def cls_override(cls) -> int:
        return 3

    @staticmethod
    @override
    def static_override() -> int:
        return 4


# Callable wrapped by non-function object with __wrapped__
def _wrap(fn):
    class Wrapper:
        def __init__(self, f):
            self._f = f
            self.__wrapped__ = f

        def __call__(self, *a, **kw):
            return self._f(*a, **kw)

    return Wrapper(fn)


@_wrap
def wrapped_callable(x: int, y: str) -> str: ...


# Nested class annotation should be fully qualified
class NestedOuter:
    class Inner:
        pass


def nested_class_annotation(x: NestedOuter.Inner) -> NestedOuter.Inner:
    return x


# Nested class from external module should import base name only
def external_nested_class_annotation(
    x: ExternalOuter.Inner,
) -> ExternalOuter.Inner:
    return x


# NamedTuple should list its fields
class PointNT(NamedTuple):
    x: int
    y: int


# __orig_bases__ mismatch should not override declared bases
class Unrelated:
    pass


class BaseModel:
    pass


class StdModel(BaseModel):
    pass


class Repeater(StdModel):
    pass


# Simulate frameworks that replace __orig_bases__ with an unrelated generic
StdModel.__orig_bases__ = (Unrelated,)  # type: ignore[attr-defined]
Repeater.__orig_bases__ = (Unrelated,)  # type: ignore[attr-defined]


# Overloaded classmethod should retain parameters
class OverloadedClassMethod:
    @overload
    @classmethod
    def get_by_id(cls, model_id: None) -> None: ...

    @overload
    @classmethod
    def get_by_id(cls, model_id: int) -> Self: ...

    @classmethod
    def get_by_id(cls, model_id: int | None) -> Self | None:
        return None if model_id is None else cls()


# __orig_bases__ supertype should not override declared base
class TopBase:
    pass


class MidBase(TopBase):
    pass


class BotBase(MidBase):
    pass


BotBase.__orig_bases__ = (TopBase,)  # type: ignore[attr-defined]


# dataclass_transform: carrier and subclass

# dataclass_transform: attribute triggers decorator and import


class DCTransformBase:
    __dataclass_transform__ = {}

    def __init_subclass__(cls) -> None:
        dataclass(cls)


class DCTransformed(DCTransformBase):
    a: int
    b: int


# Generic overloads should preserve parameterized arguments and emit base case
T1 = TypeVar("T1")
T2 = TypeVar("T2")


class TypedReturnsRows(Generic[T]):
    pass


@overload
def first[T](query: TypedReturnsRows[tuple[T]]) -> T | None: ...


@overload
def first[T1, T2, *Ts](
    query: TypedReturnsRows[tuple[T1, T2, *Ts]],
) -> tuple[T1, T2, *Ts] | None: ...


def first(query):
    return None


@overload
def one[T](query: TypedReturnsRows[tuple[T]]) -> T: ...


@overload
def one[T1, T2, *Ts](query: TypedReturnsRows[tuple[T1, T2, *Ts]]) -> tuple[T1, T2, *Ts]: ...


def one(query):
    return None


# Custom class overriding __class_getitem__ and subclass inheriting it
class CustomCG:
    def __class_getitem__(cls, item):
        return cls


class CustomCGChild(CustomCG):
    pass


# Direct and inherited recovery of custom generics
CUSTOM_CG_DIRECT: CustomCG[int]
CUSTOM_CG_CHILD_DIRECT: CustomCGChild[int]

# SQLAlchemy Result generic without string annotation
SA_RESULT_DIRECT: SAResult[int]


# Function return with type parameter and custom ``__class_getitem__``
def custom_cg_with_type_param[Model](model: type[Model]) -> CustomCG[tuple[Model]]:
    raise NotImplementedError


# SQLAlchemy generics should preserve type arguments when used as parameters
def count[T](query: "SASelect[tuple[T]]") -> int:
    return 0


def scalar[T](query: "SATypedReturnsRows[tuple[T]]") -> T:
    raise NotImplementedError


# Tuple of various SQLAlchemy generics without string annotations
SA_GENERIC_TUPLE_DIRECT: tuple[
    SAResult[int],
    SAReturnsRows[int],
    SAAliasedReturnsRows[int],
    SAExecutableReturnsRows[int],
    SASelect[int],
    SATypedReturnsRows[int],
]


# Overloaded function combining SQLAlchemy TypedReturnsRows and generics
@overload
def SATRR_first[T](query: SATypedReturnsRows[tuple[T]]) -> T | None: ...


@overload
def SATRR_first[T1, T2, *Ts](
    query: SATypedReturnsRows[tuple[T1, T2, Unpack[Ts]]],
) -> tuple[T1, T2, Unpack[Ts]] | None: ...


def SATRR_first(query):
    return None


if typing.TYPE_CHECKING:
    from fractions import Fraction as TCFraction  # used via forward ref below


class UsesTypeCheckingImport:
    val: "TCFraction"

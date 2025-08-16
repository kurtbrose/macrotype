import functools
import re
from dataclasses import InitVar, dataclass
from enum import Enum, IntEnum, IntFlag
from functools import cached_property
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
    Never,
    NewType,
    NoReturn,
    NotRequired,
    Optional,
    ParamSpec,
    Protocol,
    Required,
    Self,
    TypeAlias,
    TypeAliasType,
    TypedDict,
    TypeVar,
    TypeVarTuple,
    Union,
    Unpack,
    overload,
    override,
    runtime_checkable,
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


# Basic callable examples
def sum_of(*args: tuple[int]) -> int:
    return sum(args)


def dict_echo(**kwargs: dict[str, Any]) -> dict[str, Any]:
    return kwargs


# Edge case: direct use of ``P.args`` and ``P.kwargs``
def use_params(func: Callable[P, int], *args: P.args, **kwargs: P.kwargs) -> int:
    return func(*args, **kwargs)


# Edge case: function explicitly returning ``None``
def do_nothing() -> None:
    return None


# Functions with special control flow
def always_raises() -> NoReturn:
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
LITERAL_STR_VAR: Literal["hi"] = "hi"

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

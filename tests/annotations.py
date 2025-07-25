import re
import sys
import functools
import math
from functools import cached_property
from dataclasses import dataclass, InitVar
from enum import Enum, IntEnum, IntFlag
import collections.abc as cabc
from typing import (
    Annotated,
    Callable,
    ClassVar,
    Final,
    NoReturn,
    Never,
    NamedTuple,
    Optional,
    Union,
    Generic,
    TypeVar,
    ParamSpec,
    NewType,
    TypedDict,
    Literal,
    LiteralString,
    Self,
    TypeVarTuple,
    Unpack,
    Concatenate,
    Tuple,
    Any,
    TypeAlias,
    TypeAliasType,
    NotRequired,
    Required,
    Protocol,
    runtime_checkable,
    TypeGuard,
    final,
    override,
)
from macrotype.meta_types import (
    emit_as,
    make_literal_map,
    set_module,
    get_caller_module,
)

T = TypeVar("T")
P = ParamSpec("P")
Ts = TypeVarTuple("Ts")
# Bound type variable ensures bound metadata is ignored
U = TypeVar("U", bound=str)
# Constrained type variable ensures constraint metadata is ignored
NumberLike = TypeVar("NumberLike", int, float)
CovariantT = TypeVar("CovariantT", covariant=True)
ContravariantT = TypeVar("ContravariantT", contravariant=True)
InferredT = TypeVar("InferredT", infer_variance=True)
TDV = TypeVar("TDV")
UserId = NewType("UserId", int)

MyList: TypeAlias = list[int]
type StrList = list[str]

# Chain of generic type aliases for regression testing
type Alias0[T] = list[T]
type Alias1[T] = Alias0[T]

# Additional alias shapes
type AliasNewType = UserId
type AliasTypeVar[T] = T
type AliasUnion = int | str
type ListOrSet[T] = list[T] | set[T]
type IntFunc[**P] = Callable[P, int]
type LabeledTuple[*Ts] = tuple[str, *Ts]
type RecursiveList[T] = T | list[RecursiveList[T]]

# Edge case: alias referencing a forward-declared class
ForwardAlias: TypeAlias = "FutureClass"

# Edge case: alias defined via ``TypeAliasType`` for a TypeVar alias
AliasListT = TypeAliasType("AliasListT", list[T], type_params=(T,))
# Edge case: ``TypeAliasType`` used with a ``ParamSpec`` alias
AliasFuncP = TypeAliasType("AliasFuncP", Callable[P, int], type_params=(P,))
# Edge case: ``TypeAliasType`` used with a ``TypeVarTuple`` alias
AliasTupleTs = TypeAliasType("AliasTupleTs", tuple[*Ts], type_params=(Ts,))
# Edge case: ``TypeAliasType`` with constrained and bound type variables
AliasNumberLikeList = TypeAliasType(
    "AliasNumberLikeList", list[NumberLike], type_params=(NumberLike,)
)
AliasBoundU = TypeAliasType("AliasBoundU", list[U], type_params=(U,))

GLOBAL: int
CONST: Final[str]
# Variable typed ``Any`` to ensure explicit Any is preserved
ANY_VAR: Any
# Variable using ``Callable`` with ellipsis argument list
FUNC_ELLIPSIS: Callable[..., int]
# Variable using tuple ellipsis syntax
TUPLE_VAR: tuple[int, ...]

# Edge case: annotated constants with values should honor the annotation
ANNOTATED_FINAL: Final[int] = 5
ANNOTATED_CLASSVAR: ClassVar[int] = 1

# Edge case: unannotated constant should be included
UNANNOTATED_CONST = 42

# Edge case: lambda expressions should be treated as variables, not functions
UNTYPED_LAMBDA = lambda x, y: x + y
TYPED_LAMBDA: Callable[[int, int], int] = lambda a, b: a + b


class Basic:
    simple: list[str]
    mapping: dict[str, int]
    optional: Optional[int]
    union: Union[int, str]
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


# Edge case: Generic TypedDict should retain type parameters
class GenericBox(TypedDict, Generic[TDV]):
    item: TDV


class GenericClass(Generic[T]):
    value: T

    def get(self) -> T:
        return self.value


class Slotted:
    __slots__ = ("x", "y")
    x: int
    y: str


# Edge case: ``functools.partialmethod`` should generate a normal method stub
class HasPartialMethod:
    def base(self, a: int, b: str) -> str:
        return b * a

    pm = functools.partialmethod(base, 2)


def make_wrapper(t: type):
    class Wrapper:
        value: t

    return Wrapper


GeneratedInt = make_wrapper(int)
GeneratedPattern = make_wrapper(re.Pattern[str])


from typing import overload


@overload
def over(x: int) -> int: ...


@overload
def over(x: str) -> str: ...


def over(x: int | str) -> int | str:
    return x

# Overloads generated in a loop
for typ in (bytes, bytearray):
    @overload
    def loop_over(x: typ) -> str: ...

del typ

def loop_over(x: bytes | bytearray) -> str:
    return str(x)


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

    def __post_init__(self, init_only: int) -> None:
        self.x += init_only


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


class NewGeneric[T]:
    value: T

    def get(self) -> T:
        return self.value


class OldGeneric(Generic[T]):
    value: T

    def get(self) -> T:
        return self.value


# PEP 695 class with a bounded type parameter
class BoundClass[T: int]:
    value: T


# PEP 695 class with constrained type parameter
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


class NamedPoint(NamedTuple):
    x: int
    y: int


def use_tuple(tp: tuple[int, ...]) -> tuple[int, ...]:
    return tp


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


def as_tuple(*args: Unpack[Ts]) -> Tuple[Unpack[Ts]]:
    return tuple(args)


class Variadic(Generic[*Ts]):
    def __init__(self, *args: Unpack[Ts]) -> None:
        self.args = tuple(args)

    def to_tuple(self) -> Tuple[Unpack[Ts]]:
        return self.args


class Info(TypedDict):
    name: str
    age: int


def with_kwargs(**kwargs: Unpack[Info]) -> Info:
    return kwargs


def sum_of(*args: tuple[int]) -> int:
    return sum(args)


def dict_echo(**kwargs: dict[str, Any]) -> dict[str, Any]:
    return kwargs


# Edge case: ``Concatenate`` parameter handling
def prepend_one(fn: Callable[Concatenate[int, P], int]) -> Callable[P, int]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> int:
        return fn(1, *args, **kwargs)

    return inner


# Edge case: direct use of ``P.args`` and ``P.kwargs``
def use_params(*args: P.args, **kwargs: P.kwargs) -> int:
    return 0


# Edge case: function explicitly returning ``None``
def do_nothing() -> None:
    return None


def always_raises() -> NoReturn:
    raise RuntimeError()


def never_returns() -> Never:
    raise RuntimeError()


# Edge case: ``TypeGuard`` return type
def is_str_list(val: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(v, str) for v in val)


# Edge case: LiteralString handling
LITERAL_STR_VAR: LiteralString

# Edge case: ``Final`` annotated variables with values
FINAL_VAR_WITH_VALUE: Final[int] = 5
PLAIN_FINAL_VAR: Final = 1

# Edge case: alias to a foreign function should be preserved
SIN_ALIAS = math.sin

# Edge case: alias to a foreign constant should retain its type
PI_ALIAS = math.pi


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
def final_func(x: int) -> int:
    return x


@final
class FinalClass: ...


class HasFinalMethod:
    @final
    def do_final(self) -> None:
        pass


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


class FutureClass: ...


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
emitted_b = make_emitter("emitted_b")


# Test emit_as decorator for classes
def make_emitter_cls(name: str):
    @emit_as(name)
    class Inner:
        value: int

    return Inner


EmittedCls = make_emitter_cls("EmittedCls")


# Use emit_as with overloads defined dynamically on a class via API helper
EmittedMap = make_literal_map("EmittedMap", {"a": 1, "b": 2})

# Demonstrate adjusting a dynamically created class using helpers
def make_dynamic_cls():
    cls = type("FixedModuleCls", (), {"__module__": "tests.factory"})
    set_module(cls, get_caller_module())
    return cls

FixedModuleCls = make_dynamic_cls()

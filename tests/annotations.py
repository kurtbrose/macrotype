import re
from functools import cached_property
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import (
    Annotated,
    Callable,
    ClassVar,
    NamedTuple,
    Optional,
    Union,
    Generic,
    TypeVar,
    ParamSpec,
    NewType,
    TypedDict,
    Literal,
    Self,
    TypeVarTuple,
    Unpack,
    Tuple,
    Any,
    TypeAlias,
)

T = TypeVar("T")
P = ParamSpec("P")
Ts = TypeVarTuple("Ts")
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

    class Nested:
        x: float
        y: str


class Child(Basic):
    ...


class SampleDict(TypedDict):
    name: str
    age: int


class PartialDict(TypedDict, total=False):
    id: int
    hint: str


class GenericClass(Generic[T]):
    value: T

    def get(self) -> T:
        return self.value


class Slotted:
    __slots__ = ("x", "y")
    x: int
    y: str


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


@dataclass
class Point:
    x: int
    y: int


@dataclass(frozen=True, slots=True)
class Frozen:
    a: int
    b: int


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


def use_tuple(tp: tuple[int, ...]) -> tuple[int, ...]:
    return tp


class SelfExample:
    def clone(self: Self) -> Self:
        return self


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


# from https://docs.python.org/3.13/reference/compound_stmts.html#type-params
def overly_generic[
    SimpleTypeVar,
    TypeVarWithBound: int,
    TypeVarWithConstraints: (str, bytes),
    TypeVarWithDefault = int,
    *SimpleTypeVarTuple = (int, float),
    **SimpleParamSpec = (str, bytearray),
](
    a: SimpleTypeVar,
    b: TypeVarWithDefault,
    c: TypeVarWithBound,
    d: Callable[SimpleParamSpec, TypeVarWithConstraints],
    *e: SimpleTypeVarTuple,
) -> None:
    ...

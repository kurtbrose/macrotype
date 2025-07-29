import collections.abc as cabc
import functools
import math
from dataclasses import InitVar, dataclass
from functools import cached_property
from typing import (
    Any,
    Callable,
    ClassVar,
    Concatenate,
    Final,
    Generic,
    Literal,
    LiteralString,
    NoReturn,
    ParamSpec,
    TypeGuard,
    TypeVar,
    TypeVarTuple,
    Unpack,
    final,
    overload,
    override,
)
from macrotype.meta_types import (
    emit_as,
    get_caller_module,
    make_literal_map,
    overload as meta_overload,
    set_module,
)

T = TypeVar("T")
P = ParamSpec("P")
Ts = TypeVarTuple("Ts")
InferredT = TypeVar("InferredT", infer_variance=True)
TDV = TypeVar("TDV")

ANNOTATED_CLASSVAR: ClassVar[int] = 1

class OverrideChild(Basic):
    @override
    def copy(self, param: T) -> T:
        return param

class OverrideLate(Basic):
    @override
    @classmethod
    def cls_override(cls) -> int:
        return 1

    @override
    @staticmethod
    def static_override() -> int:
        return 2

for typ in (bytes, bytearray):

    @overload
    def loop_over(x: typ) -> str: ...


del typ

def loop_over(x: bytes | bytearray) -> str:
    return str(x)

@dataclass
class InitVarExample:
    x: int
    init_only: InitVar[int]

    def __post_init__(self, init_only: int) -> None:
        self.x += init_only

def as_tuple(*args: Unpack[Ts]) -> tuple[Unpack[Ts]]:
    return tuple(args)

class Variadic(Generic[*Ts]):
    def __init__(self, *args: Unpack[Ts]) -> None:
        self.args = tuple(args)

    def to_tuple(self) -> tuple[Unpack[Ts]]:
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

def prepend_one(fn: Callable[Concatenate[int, P], int]) -> Callable[P, int]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> int:
        return fn(1, *args, **kwargs)

    return inner

def use_params(*args: P.args, **kwargs: P.kwargs) -> int:
    return 0

def do_nothing() -> None:
    return None

def always_raises() -> NoReturn:
    raise RuntimeError()

def never_returns() -> Never:
    raise RuntimeError()

def is_str_list(val: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(v, str) for v in val)

LITERAL_STR_VAR: LiteralString
FINAL_VAR_WITH_VALUE: Final[int] = 5
PLAIN_FINAL_VAR: Final = 1
SIN_ALIAS = math.sin
PI_ALIAS = math.pi

def local_alias_target(x: int) -> int:
    return x

LOCAL_ALIAS = local_alias_target

def echo_literal(value: LiteralString) -> LiteralString:
    return value

NONE_VAR: None = None

async def async_add_one(x: int) -> int:
    return x + 1

async def gen_range(n: int) -> cabc.AsyncIterator[int]:
    for i in range(n):
        yield i

@final
def final_func(x: int) -> int:
    return x

EmittedMap = make_literal_map("EmittedMap", {"a": 1, "b": 2})

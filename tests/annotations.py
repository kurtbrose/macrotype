# pyright: basic
# mypy: allow-any-expr
import collections.abc as cabc
import functools
import math
import sys
import types
import typing
from abc import ABC, abstractmethod
from functools import cached_property
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Callable,
    Final,
    Generic,
    LiteralString,
    Never,
    NewType,
    NoReturn,
    ParamSpec,
    TypeGuard,
    TypeVar,
    TypeVarTuple,
    Unpack,
    final,
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

T = TypeVar("T")
P = ParamSpec("P")
Ts = TypeVarTuple("Ts")
# Bound type variable ensures bound metadata is ignored
U = TypeVar("U", bound=str)
# Constrained type variable ensures constraint metadata is ignored
NumberLike = TypeVar("NumberLike", int, float)
CovariantT = TypeVar("CovariantT", covariant=True)
ContravariantT = TypeVar("ContravariantT", contravariant=True)
TDV = TypeVar("TDV")
UserId = NewType("UserId", int)


def sum_of(*args: tuple[int]) -> int:
    return sum(args)


def dict_echo(**kwargs: dict[str, Any]) -> dict[str, Any]:
    return kwargs


# Edge case: ``Concatenate`` parameter handling
# Edge case: ``Concatenate`` parameter handling (requires PEP 695 generics)


# Edge case: direct use of ``P.args`` and ``P.kwargs``


def use_params(func: Callable[P, int], *args: P.args, **kwargs: P.kwargs) -> int:
    return func(*args, **kwargs)


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


# Additional TypeGuard example
def is_int(val: object) -> TypeGuard[int]:
    return isinstance(val, int)


# Edge case: LiteralString handling
LITERAL_STR_VAR: LiteralString

# Edge case: ``Final`` annotated variable with a value
PLAIN_FINAL_VAR: Final[int] = 1

# Edge case: alias to a foreign function should be preserved
SIN_ALIAS = math.sin

# Foreign function with annotation should stay a variable
COS_VAR: Callable[[float], float] = math.cos

# Edge case: alias to a foreign constant should retain its type
PI_ALIAS = math.pi

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


# Default argument example to ensure defaults are applied in overloads
@overload_for(3)
def times_two(val: int, factor: int = 2) -> int:
    return val * factor


# Edge case: overload_for should support boolean literals
@overload_for(True)
@overload_for(False)
def bool_gate(flag: bool) -> int:
    return 1 if flag else 0


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


# meta_types with inherited annotations
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

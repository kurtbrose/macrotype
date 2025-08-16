# Generated via: macrotype tests/annotations.py -o tests/annotations.pyi
# Do not edit by hand
# pyright: basic
# mypy: allow-any-expr
from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from functools import cached_property
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Callable,
    Final,
    Literal,
    LiteralString,
    NewType,
    ParamSpec,
    TypeVar,
    TypeVarTuple,
    Unpack,
    overload,
)

T = TypeVar("T")

P = ParamSpec("P")

Ts = TypeVarTuple("Ts")

U = TypeVar("U")

NumberLike = TypeVar("NumberLike")

CovariantT = TypeVar("CovariantT", covariant=True)

ContravariantT = TypeVar("ContravariantT", contravariant=True)

TDV = TypeVar("TDV")

UserId = NewType("UserId", int)

def pos_only_func(a: int, b: str, /) -> None: ...
def kw_only_func(*, x: int, y: str) -> None: ...
def pos_and_kw(a: int, /, b: int, *, c: int) -> None: ...
def iter_sequence(seq: Sequence[int]) -> Iterator[int]: ...
def simple_wrap(fn: Callable[[int], int]) -> Callable[[int], int]: ...
def double_wrapped(x: int) -> int: ...
def cached_add(a: int, b: int) -> int: ...
def annotated_fn(x: Annotated[int, "inp"]) -> Annotated[str, "out"]: ...

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
    id_type: type[ManagerModelId]

EmployeeModelId = NewType("EmployeeModelId", int)

class EmployeeModel(SQLBase):
    manager_id: Mapped[ManagerModelId]
    id: Mapped[EmployeeModelId]
    id_type: type[EmployeeModelId]

def strip_null(ann: Any, null: Any) -> Any: ...

class Cls:
    a: int
    b: None | float
    c: None | str
    d: bytes

class OptionalCls:
    a: None | int
    b: None | float
    c: None | str
    d: None | bytes

class RequiredCls:
    a: int
    b: float
    c: str
    d: bytes

class PickedCls:
    a: int
    b: None | float

class OmittedCls:
    a: int
    b: None | float

class FinalCls:
    a: Final[int]
    b: Final[None | float]
    c: Final[None | str]
    d: Final[bytes]

class ReplacedCls:
    a: str
    b: bool
    c: None | str
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
    b: Undefined | str

class OptionalUndefinedCls:
    a: Undefined | int
    b: Undefined | str

class RequiredUndefinedCls:
    a: int
    b: str

def _wrap(fn): ...
def wrapped_callable(x: int, y: str) -> str: ...

LITERAL_STR_VAR: LiteralString

DICT_WITH_IMPLICIT_ANY: dict[int]  # type: ignore[type-arg]  # pyright: ignore[reportInvalidTypeArguments]

DICT_LIST_VALUE: dict[str, list[int]]

UNPARAM_LIST: list

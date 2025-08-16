# Generated via: macrotype tests/annotations.py -o tests/annotations.pyi
# Do not edit by hand
# pyright: basic
# mypy: allow-any-expr
from typing import Any, Final, NewType, ParamSpec, TypeVar, TypeVarTuple

T = TypeVar("T")

P = ParamSpec("P")

Ts = TypeVarTuple("Ts")

U = TypeVar("U")

NumberLike = TypeVar("NumberLike")

CovariantT = TypeVar("CovariantT", covariant=True)

ContravariantT = TypeVar("ContravariantT", contravariant=True)

TDV = TypeVar("TDV")

UserId = NewType("UserId", int)

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

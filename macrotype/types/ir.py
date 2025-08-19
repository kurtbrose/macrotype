from __future__ import annotations

import enum
from dataclasses import dataclass, field
from types import EllipsisType
from typing import Literal, NewType, Optional, TypeAlias


@dataclass(frozen=True, kw_only=True, slots=True)
class TyAnnoTree:
    annos: tuple[object, ...]
    child: Optional[TyAnnoTree] = None

    def flatten(self) -> tuple[object, ...]:
        parts = []
        node: Optional[TyAnnoTree] = self
        while node:
            parts.extend(node.annos)
            node = node.child
        return tuple(parts)


@dataclass(frozen=True, kw_only=True, slots=True)
class TyRoot:
    ty: Ty | None  # None here for bare Final
    annotations: TyAnnoTree | None = None
    is_final: bool = False
    is_required: bool | None = None
    is_classvar: bool = False


@dataclass(frozen=True, kw_only=True, slots=True)
class Ty:
    """Base IR node (type-level AST)."""

    annotations: Optional["TyAnnoTree"] = field(default=None, repr=False)


@dataclass(frozen=True, kw_only=True, slots=True)
class TyAny(Ty):
    """The top type `Any`."""

    # e.g., `x: Any`


@dataclass(frozen=True, kw_only=True, slots=True)
class TyNever(Ty):
    """The bottom type `Never`/`NoReturn`."""

    # e.g., `def f() -> Never: ...`


@dataclass(frozen=True, kw_only=True, slots=True)
class TyType(Ty):
    """
    A (possibly annotated) regular python type, like int, MyClass, or Sequence.
    """

    type_: type


@dataclass(frozen=True, kw_only=True, slots=True)
class TyApp(Ty):
    """
    Generic application (type constructor applied to type arguments).

    Examples:
      - `list[int]` → TyApp(base=TyType(type_=list), args=(TyType(type_=int),))
      - `dict[str, bool]`
      - `Box[T]` where `Box` is user generic
      - `type[Foo]` / `typing.Type[Foo]`
    """

    base: Ty
    args: tuple[Ty, ...]


@dataclass(frozen=True, kw_only=True, slots=True)
class TyUnion(Ty):
    """
    Union type (already canonicalized in normalization).

    Examples:
      - `int | None`
      - `Union[int, str]`
    """

    options: tuple[Ty, ...]


# Literal value shape per PEP 586: primitives, Enums, and nested tuples thereof.
LitPrim: TypeAlias = int | bool | str | bytes | None | enum.Enum
LitVal: TypeAlias = LitPrim | tuple["LitVal", ...]


@dataclass(frozen=True, kw_only=True, slots=True)
class TyLiteral(Ty):
    """
    Literal values per PEP 586.

    Examples:
      - `Literal[1, "x", True]`
      - `Literal[("x", 1)]`
      - `Literal[Color.RED]` where `Color.RED` is an Enum member
    """

    values: tuple[LitVal, ...]


@dataclass(frozen=True, kw_only=True, slots=True)
class TyCallable(Ty):
    """
    Callable type. Parameters may include TyParamSpec / TyUnpack for advanced forms.

    Examples:
      - `Callable[[int, str], bool]`
      - `Callable[..., int]` (params=Ellipsis)
      - `Callable[Concatenate[int, P], str]`  (modeled via params containing TyParamSpec/Unpack)
    """

    params: tuple[Ty, ...] | EllipsisType
    ret: Ty


@dataclass(frozen=True, kw_only=True, slots=True)
class TyForward(Ty):
    """
    Unresolved forward reference (string form).

    Examples:
      - `"User"` before the class `User` is resolved
    """

    qualname: str


@dataclass(frozen=True, kw_only=True, slots=True)
class TyTypeVar(Ty):
    """
    Type variable declaration (single type parameter).

    Examples:
      - `T = TypeVar("T")`
      - bounds/constraints/variance captured here for reference and emission
    """

    name: str
    bound: Optional[Ty]
    constraints: tuple[Ty, ...]
    cov: bool
    contrav: bool


@dataclass(frozen=True, kw_only=True, slots=True)
class TyParamSpec(Ty):
    """
    ParamSpec declaration for callable parameter packs.

    Examples:
      - `P = ParamSpec("P")`
      - used in `Callable[P, Ret]` or `Concatenate[...]`
    """

    name: str
    flavor: Literal["args", "kwargs"] | None = None


@dataclass(frozen=True, kw_only=True, slots=True)
class TyTypeVarTuple(Ty):
    """
    TypeVarTuple declaration for variadic generics (PEP 646).

    Examples:
      - `Ts = TypeVarTuple("Ts")`
      - used with `Unpack[Ts]`
    """

    name: str


@dataclass(frozen=True, kw_only=True, slots=True)
class TyUnpack(Ty):
    """
    Unpack wrapper for variadic forms (PEP 646).

    Examples:
      - `tuple[Unpack[Ts]]`
      - `Callable[Concatenate[int, Unpack[P]], str]`  (where P is a ParamSpec)
    """

    inner: Ty


ParsedTy = NewType("ParsedTy", TyRoot)  # output of parse.parse
ResolvedTy = NewType("ResolvedTy", TyRoot)  # output of resolve.resolve
NormalizedTy = NewType("NormalizedTy", TyRoot)  # output of normalize.norm

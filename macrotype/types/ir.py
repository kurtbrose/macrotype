from __future__ import annotations

import enum
from dataclasses import dataclass, field
from types import EllipsisType
from typing import ClassVar, Literal, NewType, Optional, TypeAlias


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

    @property
    def base_type(self) -> type | None:
        """Underlying ``type`` if this node represents a concrete type.

        For non-generic nodes this is ``None``.
        """

        return None

    @property
    def generic_args(self) -> tuple["Ty", ...]:
        """Generic parameters applied to this type.

        Defaults to an empty tuple for non-generic nodes.
        """

        return ()

    @property
    def union_types(self) -> tuple["Ty", ...]:
        """Expanded union members represented by this node.

        Non-union nodes yield a one-element tuple containing ``self``.
        """

        return (self,)

    is_generic: ClassVar[bool] = False


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

    @property
    def base_type(self) -> type:
        return self.type_


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

    @property
    def base_type(self) -> type | None:
        return self.base.base_type

    @property
    def generic_args(self) -> tuple[Ty, ...]:
        return self.args

    is_generic: ClassVar[bool] = True


@dataclass(frozen=True, kw_only=True, slots=True)
class TyUnion(Ty):
    """
    Union type (already canonicalized in normalization).

    Examples:
      - `int | None`
      - `Union[int, str]`
    """

    options: tuple[Ty, ...]

    @property
    def union_types(self) -> tuple[Ty, ...]:
        return self.options


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


def has_type_member(ty: Ty, members: set[type]) -> bool:
    """Return ``True`` if ``ty`` contains a union member of any ``members``.

    For non-union inputs this simply checks ``ty`` itself.
    """

    return any(t.base_type in members for t in ty.union_types)


def strip_type_members(ty: Ty, members: set[type]) -> Ty:
    """Remove any union members whose base type is in ``members``.

    If removal leaves a single option, that option is returned directly. If all
    options are removed, an empty ``TyUnion`` is returned.
    """

    remaining = tuple(t for t in ty.union_types if t.base_type not in members)
    if not remaining:
        return TyUnion(options=())
    if len(remaining) == 1:
        return remaining[0]
    return TyUnion(options=remaining)


ParsedTy = NewType("ParsedTy", TyRoot)  # output of parse.parse
ResolvedTy = NewType("ResolvedTy", TyRoot)  # output of resolve.resolve
NormalizedTy = NewType("NormalizedTy", TyRoot)  # output of normalize.norm

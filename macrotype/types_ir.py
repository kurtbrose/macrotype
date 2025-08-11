from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional, TypeAlias

# =========================
# Shared helpers / metadata
# =========================


@dataclass(frozen=True)
class Provenance:
    """Non-semantic source info (for diagnostics), e.g. module/file/line."""

    module: str
    qualname: str
    file: Optional[str] = None
    line: Optional[int] = None


# Literal value shape per PEP 586: primitives, Enums, and nested tuples thereof.
LitPrim: TypeAlias = int | bool | str | bytes | None | enum.Enum
LitVal: TypeAlias = LitPrim | tuple["LitVal", ...]


# =====================
# Base node (all nodes)
# =====================


@dataclass(frozen=True, kw_only=True)
class Ty:
    """
    Base IR node (type-level AST).

    Notes:
    - `prov` is non-semantic metadata; excluded from equality/hash.
    - Passes should ignore it unless producing diagnostics.
    """

    prov: Optional[Provenance] = field(default=None, compare=False, hash=False, repr=False)


# ============================
# Use-site / expression nodes
# (appear in annotations)
# ============================


@dataclass(frozen=True, kw_only=True)
class TyAny(Ty):
    """The top type `Any`."""

    # e.g., `x: Any`


@dataclass(frozen=True, kw_only=True)
class TyNever(Ty):
    """The bottom type `Never`/`NoReturn`."""

    # e.g., `def f() -> Never: ...`


@dataclass(frozen=True, kw_only=True)
class TyName(Ty):
    """
    A named (possibly-qualified) type without applied parameters.

    Examples:
      - `int` → TyName("builtins", "int")
      - `typing.Sequence` → TyName("typing", "Sequence")
      - `MyClass` → TyName("mymod", "MyClass")
    """

    module: Optional[str]
    name: str


@dataclass(frozen=True, kw_only=True)
class TyApp(Ty):
    """
    Generic application (type constructor applied to type arguments).

    Examples:
      - `list[int]` → TyApp(base=TyName("builtins","list"), args=(TyName("builtins","int"),))
      - `dict[str, bool]`
      - `Box[T]` where `Box` is user generic
      - `type[Foo]` / `typing.Type[Foo]`
    """

    base: Ty
    args: tuple[Ty, ...]


@dataclass(frozen=True, kw_only=True)
class TyTuple(Ty):
    """
    Tuple type (fixed-length). Variadic `tuple[T, ...]` is modeled as
    `TyApp(TyName("builtins","tuple"), (T, TyName("builtins","Ellipsis"))).`

    Examples:
      - `tuple[int, str]`
    """

    items: tuple[Ty, ...]


@dataclass(frozen=True, kw_only=True)
class TyUnion(Ty):
    """
    Union type (already canonicalized in normalization).

    Examples:
      - `int | None`
      - `Union[int, str]`
    """

    options: tuple[Ty, ...]


@dataclass(frozen=True, kw_only=True)
class TyLiteral(Ty):
    """
    Literal values per PEP 586.

    Examples:
      - `Literal[1, "x", True]`
      - `Literal[("x", 1)]`
      - `Literal[Color.RED]` where `Color.RED` is an Enum member
    """

    values: tuple[LitVal, ...]


@dataclass(frozen=True, kw_only=True)
class TyAnnotated(Ty):
    """
    Annotated type per PEP 593; metadata are arbitrary Python objects.

    Examples:
      - `Annotated[int, "units:ms"]`
      - `typing.Annotated[str, SomeMarker()]`
    """

    base: Ty
    anno: tuple[object, ...]


@dataclass(frozen=True, kw_only=True)
class TyCallable(Ty):
    """
    Callable type. Parameters may include TyParamSpec / TyUnpack for advanced forms.

    Examples:
      - `Callable[[int, str], bool]`
      - `Callable[..., int]` (params=Ellipsis)
      - `Callable[Concatenate[int, P], str]`  (modeled via params containing TyParamSpec/Unpack)
    """

    params: tuple[Ty, ...] | Ellipsis
    ret: Ty


@dataclass(frozen=True, kw_only=True)
class TyClassVar(Ty):
    """
    ClassVar wrapper for class attributes.

    Examples:
      - `ClassVar[int]`
    """

    inner: Ty


@dataclass(frozen=True, kw_only=True)
class TyForward(Ty):
    """
    Unresolved forward reference (string form).

    Examples:
      - `"User"` before the class `User` is resolved
    """

    qualname: str


# TypedDict (use-site type, but its fields are declaration-like; see TyTDItem)


@dataclass(frozen=True, kw_only=True)
class TyTDItem:
    """
    One TypedDict field with required/optional flag and its own provenance.

    Examples:
      - key="id", ty=int, required=True
    """

    name: str
    ty: Ty
    required: bool
    prov: Optional[Provenance] = field(default=None, compare=False, hash=False, repr=False)


@dataclass(frozen=True, kw_only=True)
class TyTypedDict(Ty):
    """
    TypedDict type. `items` enumerate fields if constructed inline; or `name` points
    to a nominal TD elsewhere (items may be empty in that case).

    Examples:
      - Inline:
          TypedDict("User", {"id": int, "name": str}, total=True)
        → TyTypedDict(name="User", items=[...], total=True)
      - Nominal reference:
          class User(TypedDict): ...
        → TyName("mymod","User") at use-site (preferred), but TyTypedDict can model inline generation.
    """

    name: Optional[str]
    items: tuple[TyTDItem, ...]
    total: bool


# ==================================
# Declaration-site / binder nodes
# (appear in generic parameter lists)
# ==================================


@dataclass(frozen=True, kw_only=True)
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


@dataclass(frozen=True, kw_only=True)
class TyParamSpec(Ty):
    """
    ParamSpec declaration for callable parameter packs.

    Examples:
      - `P = ParamSpec("P")`
      - used in `Callable[P, Ret]` or `Concatenate[...]`
    """

    name: str


@dataclass(frozen=True, kw_only=True)
class TyTypeVarTuple(Ty):
    """
    TypeVarTuple declaration for variadic generics (PEP 646).

    Examples:
      - `Ts = TypeVarTuple("Ts")`
      - used with `Unpack[Ts]`
    """

    name: str


@dataclass(frozen=True, kw_only=True)
class TyUnpack(Ty):
    """
    Unpack wrapper for variadic forms (PEP 646).

    Examples:
      - `tuple[Unpack[Ts]]`
      - `Callable[Concatenate[int, Unpack[P]], str]`  (where P is a ParamSpec)
    """

    inner: Ty

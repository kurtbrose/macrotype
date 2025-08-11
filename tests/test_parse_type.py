from __future__ import annotations

import enum
import typing as t

from macrotype.parse_type import to_ir
from macrotype.types_ir import (
    Ty,
    TyAnnotated,
    TyAny,
    TyApp,
    TyCallable,
    TyClassVar,
    TyForward,
    TyLiteral,
    TyName,
    TyNever,
    TyParamSpec,
    TyTuple,
    TyTypeVar,
    TyTypeVarTuple,
    TyUnion,
    TyUnpack,
)


# ----- helpers -----
def b(name: str) -> TyName:
    return TyName(module="builtins", name=name)


def typ(name: str) -> TyName:
    return TyName(module="typing", name=name)


# ----- fixtures used in tests -----
class Color(enum.Enum):
    RED = 1
    BLUE = 2


T = t.TypeVar("T")
P = t.ParamSpec("P")
Ts = t.TypeVarTuple("Ts")


# user generic
class Box(t.Generic[T]):  # noqa: D401
    """A simple generic for tests."""

    pass


# PEP 695 alias if available (Python 3.12+)
AliasListT = None
if hasattr(t, "TypeAliasType"):
    AliasListT = t.TypeAliasType("AliasListT", list[T], type_params=(T,))  # type: ignore[name-defined]


# ----- table-driven positive cases -----
CASES: list[tuple[object, Ty]] = [
    # atoms / basics
    (int, b("int")),
    (str, b("str")),
    (None, b("None")),
    (t.Any, TyAny()),
    (t.NoReturn, TyNever()),
    (t.Never, TyNever()),
    (t.LiteralString, typ("LiteralString")),
    # Literal (PEP 586 shapes)
    (t.Literal[1, "x", True, None], TyLiteral(values=(1, "x", True, None))),
    (t.Literal[Color.RED], TyLiteral(values=(Color.RED,))),
    # builtins and common generics
    (dict, b("dict")),
    (list, b("list")),
    (tuple, b("tuple")),
    (set, b("set")),
    (frozenset, b("frozenset")),
    (dict[int], TyApp(base=b("dict"), args=(b("int"),))),
    (dict[int, str], TyApp(base=b("dict"), args=(b("int"), b("str")))),
    (dict[int, t.Any], TyApp(base=b("dict"), args=(b("int"), TyAny()))),
    (list[int], TyApp(base=b("list"), args=(b("int"),))),
    (
        list[list[int]],
        TyApp(base=b("list"), args=(TyApp(base=b("list"), args=(b("int"),)),)),
    ),
    (
        dict[str, list[int]],
        TyApp(base=b("dict"), args=(b("str"), TyApp(base=b("list"), args=(b("int"),)))),
    ),
    # tuples
    (tuple[()], TyTuple(items=())),
    (tuple[int], TyTuple(items=(b("int"),))),
    (tuple[int, str], TyTuple(items=(b("int"), b("str")))),
    # variadic as application with Ellipsis marker
    (tuple[int, ...], TyApp(base=b("tuple"), args=(b("int"), b("Ellipsis")))),
    (
        tuple[int, str, ...],
        TyApp(base=b("tuple"), args=(b("int"), b("str"), b("Ellipsis"))),
    ),
    # Unpack in tuples
    (t.Unpack[Ts], TyUnpack(inner=TyTypeVarTuple(name="Ts"))),
    (tuple[t.Unpack[Ts]], TyTuple(items=(TyUnpack(inner=TyTypeVarTuple(name="Ts")),))),
    # sets
    (set[int], TyApp(base=b("set"), args=(b("int"),))),
    (frozenset[str], TyApp(base=b("frozenset"), args=(b("str"),))),
    # unions / optionals
    (t.Union[int, str], TyUnion(options=(b("int"), b("str")))),
    (int | str, TyUnion(options=(b("int"), b("str")))),
    (t.Union[int, str, None], TyUnion(options=(b("None"), b("int"), b("str")))),
    (
        dict[str, t.Union[int, None]],
        TyApp(base=b("dict"), args=(b("str"), TyUnion(options=(b("None"), b("int"))))),
    ),
    # callables
    (t.Callable[[int, str], bool], TyCallable(params=(b("int"), b("str")), ret=b("bool"))),
    (t.Callable[..., int], TyCallable(params=..., ret=b("int"))),
    (
        t.Callable[P, int],
        TyCallable(params=(TyParamSpec(name="P"),), ret=b("int")),
    ),
    (
        t.Concatenate[int, P],
        TyApp(base=typ("Concatenate"), args=(b("int"), TyParamSpec(name="P"))),
    ),
    (
        t.Callable[t.Concatenate[int, P], int],
        TyCallable(
            params=(
                TyApp(
                    base=typ("Concatenate"),
                    args=(b("int"), TyParamSpec(name="P")),
                ),
            ),
            ret=b("int"),
        ),
    ),
    # Annotated
    (t.Annotated[int, "x"], TyAnnotated(base=b("int"), anno=("x",))),
    # ClassVar / Final / Required / NotRequired (IR unwraps Final/Req)
    (t.ClassVar[int], TyClassVar(inner=b("int"))),
    (t.Final[int], b("int")),  # Final is handled at the symbol layer
    (t.Final, TyAny()),  # bare Final → inner Any here (symbol layer will infer/wrap)
    (t.NotRequired[int], b("int")),
    (t.Required[str], b("str")),
    # variables / binders (declaration-like leaves appearing at use sites)
    (
        T,
        TyTypeVar(name="T", bound=None, constraints=(), cov=False, contrav=False),
    ),
    (P, TyParamSpec(name="P")),
    (Ts, TyTypeVarTuple(name="Ts")),
    (t.Unpack[Ts], TyUnpack(inner=TyTypeVarTuple(name="Ts"))),
    # typing.Type / builtins.type
    (t.Type[int], TyApp(base=b("type"), args=(b("int"),))),
    # forward ref by string
    ("User", TyForward(qualname="User")),
    # collections.abc generics parse (kept as names/apps; normalization can fold later)
    (t.Deque[int], TyApp(base=typ("Deque"), args=(b("int"),))),
]

# Optional cases depending on runtime features
if AliasListT is not None:
    CASES.append(
        (
            AliasListT[int],
            TyApp(base=TyName(module=__name__, name="AliasListT"), args=(b("int"),)),
        )
    )


def test_parse_table_driven():
    assert CASES == [(src, to_ir(src)) for src, _ in CASES]


def test_user_generic_application():
    got = to_ir(Box[int])
    assert isinstance(got, TyApp)
    assert isinstance(got.base, TyName)
    assert got.base.name == "Box" and got.base.module == Box.__module__
    assert got.args == (b("int"),)


def test_union_order_insensitive():
    a = to_ir(int | str)
    b = to_ir(str | int)
    assert a == b

from __future__ import annotations

import enum
import typing as t

import pytest

from macrotype.types.ir import (
    Ty,
    TyAnnoTree,
    TyAny,
    TyApp,
    TyCallable,
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
from macrotype.types.parse import _append_ann_child, parse


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
    (
        t.Annotated[int, "x"],
        TyName(module="builtins", name="int", annotations=TyAnnoTree(annos=("x",))),
    ),
    # ClassVar / Final / Required / NotRequired
    (t.ClassVar[int], b("int")),
    (t.Final[int], b("int")),
    (t.Final, TyAny()),
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

FLAGS = {
    repr(t.ClassVar[int]): (False, None, True),
    repr(t.Final[int]): (True, None, False),
    repr(t.Final): (True, None, False),
    repr(t.NotRequired[int]): (False, False, False),
    repr(t.Required[str]): (False, True, False),
}

# Optional cases depending on runtime features
if AliasListT is not None:
    CASES.append(
        (
            AliasListT[int],
            TyApp(base=TyName(module=__name__, name="AliasListT"), args=(b("int"),)),
        )
    )


def test_parse_table_driven():
    assert CASES == [(src, parse(src).ty) for src, _ in CASES]
    for src, _ in CASES:
        got = parse(src)
        is_final, is_required, is_classvar = FLAGS.get(repr(src), (False, None, False))
        assert got.is_final is is_final
        assert got.is_required is is_required
        assert got.is_classvar is is_classvar


def test_user_generic_application():
    got = parse(Box[int]).ty
    assert isinstance(got, TyApp)
    assert isinstance(got.base, TyName)
    assert got.base.name == "Box" and got.base.module == Box.__module__
    assert got.args == (b("int"),)


def test_append_ann_child():
    inner = TyAnnoTree(annos=("a",))
    outer = TyAnnoTree(annos=("b",))
    merged = _append_ann_child(inner, outer)
    assert merged.annos == ("a",)
    assert merged.child and merged.child.annos == ("b",)


def test_union_order_insensitive():
    a = parse(int | str)
    b = parse(str | int)
    assert a == b


def test_inner_final_disallowed():
    with pytest.raises(ValueError):
        parse(list[t.Final[int]])

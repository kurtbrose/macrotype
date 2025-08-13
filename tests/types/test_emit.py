from __future__ import annotations

import builtins
import typing as t
from types import EllipsisType

from macrotype.types.emit import EmitCtx, emit_top
from macrotype.types.ir import (
    TyAnnoTree,
    TyAny,
    TyApp,
    TyCallable,
    TyLiteral,
    TyNever,
    TyRoot,
    TyType,
    TyTypeVarTuple,
    TyUnion,
    TyUnpack,
)


def b(n: str) -> TyType:
    if n == "Ellipsis":
        return TyType(type_=EllipsisType)
    if n == "None":
        return TyType(type_=type(None))
    return TyType(type_=getattr(builtins, n))


def typ(n: str) -> TyType:
    return TyType(type_=getattr(t, n))


CASES: list[tuple[TyRoot, str, set[str]]] = [
    (TyRoot(ty=TyAny()), "Any", {"Any"}),
    (TyRoot(ty=TyNever()), "Never", {"Never"}),
    (TyRoot(ty=TyUnion(options=(b("int"), b("None")))), "int | None", set()),
    (TyRoot(ty=TyApp(base=b("list"), args=(b("str"),))), "list[str]", set()),
    (TyRoot(ty=TyLiteral(values=(1, "x"))), "Literal[1, 'x']", {"Literal"}),
    (
        TyRoot(ty=TyType(type_=int, annotations=TyAnnoTree(annos=("x",)))),
        "Annotated[int, 'x']",
        {"Annotated"},
    ),
    (
        TyRoot(
            ty=TyType(
                type_=int,
                annotations=TyAnnoTree(annos=("a",), child=TyAnnoTree(annos=("b",))),
            )
        ),
        "Annotated[Annotated[int, 'b'], 'a']",
        {"Annotated"},
    ),
    (
        TyRoot(ty=TyCallable(params=(b("int"),), ret=b("bool"))),
        "Callable[[int], bool]",
        {"Callable"},
    ),
    (TyRoot(ty=TyCallable(params=..., ret=b("int"))), "Callable[..., int]", {"Callable"}),
    (
        TyRoot(ty=b("int"), is_classvar=True),
        "ClassVar[int]",
        {"ClassVar"},
    ),
    (
        TyRoot(ty=TyApp(base=b("tuple"), args=(b("int"), b("Ellipsis")))),
        "tuple[int, Ellipsis]",
        set(),
    ),
    (
        TyRoot(ty=TyUnpack(inner=TyTypeVarTuple(name="Ts"))),
        "Unpack[Ts]",
        {"Unpack"},
    ),
]


def test_emit_table():
    def try_emit(node):
        ctx = EmitCtx()
        out = emit_top(node, ctx)
        return out, ctx.typing_needed

    assert CASES == [(n,) + try_emit(n) for n, _, __ in CASES]

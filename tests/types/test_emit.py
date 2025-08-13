from __future__ import annotations

from macrotype.types.emit import EmitCtx, emit_top
from macrotype.types.ir import (
    Qualifier,
    TyAnnoTree,
    TyAny,
    TyApp,
    TyCallable,
    TyLiteral,
    TyName,
    TyNever,
    TyTop,
    TyTypeVarTuple,
    TyUnion,
    TyUnpack,
)


def b(n: str) -> TyName:
    return TyName(module="builtins", name=n)


def typ(n: str) -> TyName:
    return TyName(module="typing", name=n)


CASES: list[tuple[TyTop, str, set[str]]] = [
    (TyTop(ty=TyAny()), "Any", {"Any"}),
    (TyTop(ty=TyNever()), "Never", {"Never"}),
    (TyTop(ty=TyUnion(options=(b("int"), b("None")))), "int | None", set()),
    (TyTop(ty=TyApp(base=b("list"), args=(b("str"),))), "list[str]", set()),
    (TyTop(ty=TyLiteral(values=(1, "x"))), "Literal[1, 'x']", {"Literal"}),
    (
        TyTop(ty=TyName(module="builtins", name="int", annotations=TyAnnoTree(annos=("x",)))),
        "Annotated[int, 'x']",
        {"Annotated"},
    ),
    (
        TyTop(
            ty=TyName(
                module="builtins",
                name="int",
                annotations=TyAnnoTree(annos=("a",), child=TyAnnoTree(annos=("b",))),
            )
        ),
        "Annotated[Annotated[int, 'b'], 'a']",
        {"Annotated"},
    ),
    (
        TyTop(ty=TyCallable(params=(b("int"),), ret=b("bool"))),
        "Callable[[int], bool]",
        {"Callable"},
    ),
    (TyTop(ty=TyCallable(params=..., ret=b("int"))), "Callable[..., int]", {"Callable"}),
    (
        TyTop(ty=b("int"), qualifiers=frozenset({Qualifier.CLASSVAR})),
        "ClassVar[int]",
        {"ClassVar"},
    ),
    (
        TyTop(ty=TyApp(base=b("tuple"), args=(b("int"), b("Ellipsis")))),
        "tuple[int, Ellipsis]",
        set(),
    ),
    (
        TyTop(ty=TyUnpack(inner=TyTypeVarTuple(name="Ts"))),
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

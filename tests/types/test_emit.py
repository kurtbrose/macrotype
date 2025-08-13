from __future__ import annotations

from macrotype.types.emit import EmitCtx, emit_top
from macrotype.types.ir import (
    TyAnnoTree,
    TyAny,
    TyApp,
    TyCallable,
    TyLiteral,
    TyName,
    TyNever,
    TyRoot,
    TyTypeVarTuple,
    TyUnion,
    TyUnpack,
)


def b(n: str) -> TyName:
    return TyName(module="builtins", name=n)


def typ(n: str) -> TyName:
    return TyName(module="typing", name=n)


CASES: list[tuple[TyRoot, str, set[str]]] = [
    (TyRoot(ty=TyAny()), "Any", {"Any"}),
    (TyRoot(ty=TyNever()), "Never", {"Never"}),
    (TyRoot(ty=TyUnion(options=(b("int"), b("None")))), "int | None", set()),
    (TyRoot(ty=TyApp(base=b("list"), args=(b("str"),))), "list[str]", set()),
    (TyRoot(ty=TyLiteral(values=(1, "x"))), "Literal[1, 'x']", {"Literal"}),
    (
        TyRoot(ty=TyName(module="builtins", name="int", annotations=TyAnnoTree(annos=("x",)))),
        "Annotated[int, 'x']",
        {"Annotated"},
    ),
    (
        TyRoot(
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

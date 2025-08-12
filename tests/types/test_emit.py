from __future__ import annotations

from macrotype.types.emit import EmitCtx, emit
from macrotype.types.ir import (
    Ty,
    TyAnnoTree,
    TyAny,
    TyApp,
    TyCallable,
    TyClassVar,
    TyLiteral,
    TyName,
    TyNever,
    TyTypeVarTuple,
    TyUnion,
    TyUnpack,
)


def b(n: str) -> TyName:
    return TyName(module="builtins", name=n)


def typ(n: str) -> TyName:
    return TyName(module="typing", name=n)


CASES: list[tuple[Ty, str, set[str]]] = [
    (TyAny(), "Any", {"Any"}),
    (TyNever(), "Never", {"Never"}),
    (TyUnion(options=(b("int"), b("None"))), "int | None", set()),
    (TyApp(base=b("list"), args=(b("str"),)), "list[str]", set()),
    (TyLiteral(values=(1, "x")), "Literal[1, 'x']", {"Literal"}),
    (
        TyName(module="builtins", name="int", annotations=TyAnnoTree(annos=("x",))),
        "Annotated[int, 'x']",
        {"Annotated"},
    ),
    (
        TyName(
            module="builtins",
            name="int",
            annotations=TyAnnoTree(annos=("a",), child=TyAnnoTree(annos=("b",))),
        ),
        "Annotated[Annotated[int, 'b'], 'a']",
        {"Annotated"},
    ),
    (TyCallable(params=(b("int"),), ret=b("bool")), "Callable[[int], bool]", {"Callable"}),
    (TyCallable(params=..., ret=b("int")), "Callable[..., int]", {"Callable"}),
    (TyClassVar(inner=b("int")), "ClassVar[int]", {"ClassVar"}),
    (TyApp(base=b("tuple"), args=(b("int"), b("Ellipsis"))), "tuple[int, Ellipsis]", set()),
    (TyUnpack(inner=TyTypeVarTuple(name="Ts")), "Unpack[Ts]", {"Unpack"}),
]


def test_emit_table():
    def try_emit(node):
        ctx = EmitCtx()
        out = emit(node, ctx)
        return out, ctx.typing_needed

    assert CASES == [(n,) + try_emit(n) for n, _, __ in CASES]

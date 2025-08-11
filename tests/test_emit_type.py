from __future__ import annotations

from macrotype.emit_type import EmitCtx, emit_type
from macrotype.types_ir import (
    Ty,
    TyAnnotated,
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
    (TyAnnotated(base=b("int"), anno=("x",)), "Annotated[int, 'x']", {"Annotated"}),
    (TyCallable(params=(b("int"),), ret=b("bool")), "Callable[[int], bool]", {"Callable"}),
    (TyCallable(params=..., ret=b("int")), "Callable[..., int]", {"Callable"}),
    (TyClassVar(inner=b("int")), "ClassVar[int]", {"ClassVar"}),
    (TyApp(base=b("tuple"), args=(b("int"), b("Ellipsis"))), "tuple[int, Ellipsis]", set()),
    (TyUnpack(inner=TyTypeVarTuple(name="Ts")), "Unpack[Ts]", {"Unpack"}),
]


def test_emit_type_table():
    def try_emit(node):
        ctx = EmitCtx()
        out = emit_type(node, ctx)
        return out, ctx.typing_needed

    assert CASES == [(n,) + try_emit(n) for n, _, __ in CASES]

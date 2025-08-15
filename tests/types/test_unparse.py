import builtins
from dataclasses import InitVar
from types import EllipsisType

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
from macrotype.types.unparse import unparse_top


def b(n: str) -> TyType:
    if n == "Ellipsis":
        return TyType(type_=EllipsisType)
    if n == "None":
        return TyType(type_=type(None))
    return TyType(type_=getattr(builtins, n))


CASES: list[tuple[TyRoot, str]] = [
    (TyRoot(ty=TyAny()), "typing.Any"),
    (TyRoot(ty=TyNever()), "typing.Never"),
    (TyRoot(ty=TyUnion(options=(b("int"), b("None")))), "int | None"),
    (TyRoot(ty=TyApp(base=b("list"), args=(b("str"),))), "list[str]"),
    (TyRoot(ty=TyLiteral(values=(1, "x"))), "typing.Literal[1, 'x']"),
    (
        TyRoot(ty=TyType(type_=int, annotations=TyAnnoTree(annos=("x",)))),
        "typing.Annotated[int, 'x']",
    ),
    (
        TyRoot(
            ty=TyType(
                type_=int,
                annotations=TyAnnoTree(annos=("a",), child=TyAnnoTree(annos=("b",))),
            )
        ),
        "typing.Annotated[int, 'a', 'b']",
    ),
    (
        TyRoot(ty=TyCallable(params=(b("int"),), ret=b("bool"))),
        "typing.Callable[[int], bool]",
    ),
    (TyRoot(ty=TyCallable(params=..., ret=b("int"))), "typing.Callable[..., int]"),
    (TyRoot(ty=b("int"), is_classvar=True), "typing.ClassVar[int]"),
    (TyRoot(ty=b("tuple")), "<class 'tuple'>"),
    (TyRoot(ty=TyApp(base=b("tuple"), args=())), "tuple[()]"),
    (TyRoot(ty=TyApp(base=b("tuple"), args=(b("int"),))), "tuple[int]"),
    (
        TyRoot(ty=TyApp(base=b("tuple"), args=(b("int"), b("Ellipsis")))),
        "tuple[int, ...]",
    ),
    (
        TyRoot(ty=TyUnpack(inner=TyTypeVarTuple(name="Ts"))),
        "typing.Unpack[Ts]",
    ),
    (
        TyRoot(ty=TyApp(base=TyType(type_=InitVar), args=(b("int"),))),
        "dataclasses.InitVar[int]",
    ),
    (
        TyRoot(
            ty=TyApp(
                base=TyType(type_=InitVar),
                args=(TyApp(base=b("list"), args=(b("int"),)),),
            )
        ),
        "dataclasses.InitVar[list[int]]",
    ),
]


def test_unparse_table() -> None:
    def try_unparse(node: TyRoot) -> str:
        out = unparse_top(node)
        return repr(out)

    assert CASES == [(n, try_unparse(n)) for n, _ in CASES]

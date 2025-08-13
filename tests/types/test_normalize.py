from __future__ import annotations

from macrotype.types.ir import (
    TyAnnoTree,
    TyAny,
    TyApp,
    TyLiteral,
    TyName,
    TyRoot,
    TyTuple,
    TyUnion,
)
from macrotype.types.normalize import norm


def b(name: str) -> TyName:  # builtins
    return TyName(module="builtins", name=name)


def typ(name: str) -> TyName:  # typing
    return TyName(module="typing", name=name)


# ---- table: (ResolvedTy -> NormalizedTy) ----
CASES = [
    # Union flatten + dedup + sort
    (
        TyUnion(options=(b("int"), TyUnion(options=(b("str"), b("int"))))),
        TyUnion(options=(b("int"), b("str"))),
    ),
    # Singleton union → element
    (
        TyUnion(options=(b("int"),)),
        b("int"),
    ),
    # Empty union → Never (policy)
    (
        TyUnion(options=()),
        b("Never"),  # we'll create as TyNever via norm; see assertion below
    ),
    # typing.List -> list
    (
        TyApp(base=typ("List"), args=(b("int"),)),
        TyApp(base=b("list"), args=(b("int"),)),
    ),
    # typing.Type -> type
    (
        TyApp(base=typ("Type"), args=(b("str"),)),
        TyApp(base=b("type"), args=(b("str"),)),
    ),
    # Annotated[Any, ...] drops to Any (default policy)
    (
        TyAny(annotations=TyAnnoTree(annos=("x",))),
        TyAny(),
    ),
    # Nested annotations preserved
    (
        TyName(
            module="builtins",
            name="int",
            annotations=TyAnnoTree(annos=("b",), child=TyAnnoTree(annos=("a",))),
        ),
        TyName(
            module="builtins",
            name="int",
            annotations=TyAnnoTree(annos=("b",), child=TyAnnoTree(annos=("a",))),
        ),
    ),
    # Literal dedup preserves first occurrence
    (
        TyLiteral(values=(1, 1, "x", "x")),
        TyLiteral(values=(1, "x")),
    ),
    # Tuple elements normalized recursively
    (
        TyTuple(items=(typ("List"),)),
        TyTuple(items=(b("list"),)),
    ),
    (
        TyTuple(items=(TyApp(base=typ("List"), args=(b("int"),)),)),
        TyTuple(items=(TyApp(base=b("list"), args=(b("int"),)),)),
    ),
]


def test_normalize_table() -> None:
    got: list[tuple[object, object]] = []
    for src, exp in CASES:
        n = norm(TyRoot(ty=src))
        if isinstance(src, TyUnion) and len(src.options) == 0:
            assert repr(n.ty) == "TyNever()", "Empty union should normalize to Never"
        else:
            got.append((src, n.ty))
    # Compare remaining
    expected = [
        pair for pair in CASES if not (isinstance(pair[0], TyUnion) and len(pair[0].options) == 0)
    ]
    assert expected == got


def test_idempotence() -> None:
    # quick fuzz over representative shapes
    reps = [
        TyUnion(options=(b("int"), TyUnion(options=(b("str"), b("int"))))),
        TyName(
            module="builtins",
            name="int",
            annotations=TyAnnoTree(annos=("b",), child=TyAnnoTree(annos=("a",))),
        ),
        TyApp(base=typ("List"), args=(b("int"),)),
        TyLiteral(values=(1, 1, "x")),
    ]
    for r in reps:
        n1 = norm(TyRoot(ty=r))
        n2 = norm(n1)
        assert n1 == n2

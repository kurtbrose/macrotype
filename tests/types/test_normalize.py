from __future__ import annotations

import builtins
import typing as t
from dataclasses import InitVar
from types import EllipsisType

from macrotype.types.ir import (
    TyAnnoTree,
    TyAny,
    TyApp,
    TyLiteral,
    TyNever,
    TyRoot,
    TyType,
    TyUnion,
)
from macrotype.types.normalize import norm


def b(name: str) -> TyType:  # builtins
    if name == "Ellipsis":
        return TyType(type_=EllipsisType)
    if name == "None":
        return TyType(type_=type(None))
    return TyType(type_=getattr(builtins, name))


def typ(name: str) -> TyType:  # typing
    return TyType(type_=getattr(t, name))


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
        TyNever(),
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
        TyType(
            type_=int,
            annotations=TyAnnoTree(annos=("b",), child=TyAnnoTree(annos=("a",))),
        ),
        TyType(
            type_=int,
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
        TyApp(base=b("tuple"), args=(typ("List"),)),
        TyApp(base=b("tuple"), args=(b("list"),)),
    ),
    (
        TyApp(base=b("tuple"), args=(TyApp(base=typ("List"), args=(b("int"),)),)),
        TyApp(base=b("tuple"), args=(TyApp(base=b("list"), args=(b("int"),)),)),
    ),
    # dataclasses.InitVar is unaffected
    (
        TyApp(base=TyType(type_=InitVar), args=(b("int"),)),
        TyApp(base=TyType(type_=InitVar), args=(b("int"),)),
    ),
]


def test_normalize_table() -> None:
    got: list[tuple[object, object]] = []
    for src, exp in CASES:
        n = norm(TyRoot(ty=src))
        got.append((src, n.ty))
    assert CASES == got


def test_idempotence() -> None:
    # quick fuzz over representative shapes
    reps = [
        TyUnion(options=(b("int"), TyUnion(options=(b("str"), b("int"))))),
        TyType(
            type_=int,
            annotations=TyAnnoTree(annos=("b",), child=TyAnnoTree(annos=("a",))),
        ),
        TyApp(base=typ("List"), args=(b("int"),)),
        TyLiteral(values=(1, 1, "x")),
    ]
    for r in reps:
        n1 = norm(TyRoot(ty=r))
        n2 = norm(n1)
        assert n1 == n2

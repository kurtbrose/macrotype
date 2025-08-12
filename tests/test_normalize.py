from __future__ import annotations

from macrotype.normalize import norm
from macrotype.types_ir import (
    TyAnnotated,
    TyAny,
    TyApp,
    TyLiteral,
    TyName,
    TyTuple,
    TyUnion,
)


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
        TyAnnotated(base=TyAny(), anno=("x",)),
        TyAny(),
    ),
    # Merge nested Annotated
    (
        TyAnnotated(base=TyAnnotated(base=b("int"), anno=("a",)), anno=("b",)),
        TyAnnotated(base=b("int"), anno=("a", "b")),
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
        n = norm(src)
        # special-case the empty-union policy expected marker above
        if isinstance(src, TyUnion) and len(src.options) == 0:
            assert repr(n) == "TyNever()", "Empty union should normalize to Never"
        else:
            got.append((src, n))
    # Compare remaining
    expected = [
        pair for pair in CASES if not (isinstance(pair[0], TyUnion) and len(pair[0].options) == 0)
    ]
    assert expected == got


def test_idempotence() -> None:
    # quick fuzz over representative shapes
    reps = [
        TyUnion(options=(b("int"), TyUnion(options=(b("str"), b("int"))))),
        TyAnnotated(base=TyAnnotated(base=b("int"), anno=("a",)), anno=("b",)),
        TyApp(base=typ("List"), args=(b("int"),)),
        TyLiteral(values=(1, 1, "x")),
    ]
    for r in reps:
        n1 = norm(r)
        n2 = norm(n1)
        assert n1 == n2

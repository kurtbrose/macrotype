from __future__ import annotations

import typing as t

from macrotype.types.ir import (
    Ty,
    TyApp,
    TyCallable,
    TyForward,
    TyName,
    TyUnion,
)
from macrotype.types.parse import parse
from macrotype.types.resolve import ResolveEnv, resolve


def b(name: str) -> TyName:
    return TyName(module="builtins", name=name)


def typ(name: str) -> TyName:
    return TyName(module="typing", name=name)


# A tiny user generic to exercise qualification/no-op paths
T = t.TypeVar("T")


class Box(t.Generic[T]):  # noqa: D401
    """Test generic."""

    pass


# ----- resolution environment -----
ENV = ResolveEnv(
    module="mymod.test",
    imports={
        "User": "pkg.models.User",
        "Box": f"{Box.__module__}.Box",  # allow qualifying bare 'Box' if it ever appears
    },
)


# ----- table: (source annotation object -> expected Resolved Ty) -----
CASES: list[tuple[object, Ty]] = [
    # 1) Forward ref as string
    ("User", TyName(module="pkg.models", name="User")),
    # 2) list["User"] → list[pkg.models.User]
    (
        list["User"],  # noqa: F821
        TyApp(base=b("list"), args=(TyName(module="pkg.models", name="User"),)),
    ),
    # 3) typing.Type["User"] → type[pkg.models.User]
    (
        t.Type["User"],  # noqa: F821
        TyApp(base=b("type"), args=(TyName(module="pkg.models", name="User"),)),
    ),
    # 4) No-op on already-qualified user generic
    (
        Box[int],
        TyApp(base=TyName(module=Box.__module__, name="Box"), args=(b("int"),)),
    ),
    # 5) Union containing forward & normal
    (
        t.Union["User", int],  # noqa: F821
        TyUnion(options=(TyName(module="pkg.models", name="User"), b("int"))),
    ),
    # 6) Callable[..., "User"]
    (
        t.Callable[..., "User"],  # noqa: F821
        TyCallable(params=..., ret=TyName(module="pkg.models", name="User")),
    ),
]


def test_resolve_table_driven():
    got = [(src, resolve(parse(src), ENV).ty) for src, _ in CASES]
    assert CASES == got


def test_unresolved_forward_remains():
    # Not in imports map → stays TyForward
    ty = resolve(parse("MissingType"), ENV).ty
    assert isinstance(ty, TyForward) and ty.qualname == "MissingType"

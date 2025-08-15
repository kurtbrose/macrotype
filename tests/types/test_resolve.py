from __future__ import annotations

import builtins
import typing as t
from dataclasses import InitVar

from macrotype.types.ir import (
    Ty,
    TyApp,
    TyCallable,
    TyForward,
    TyType,
    TyUnion,
)
from macrotype.types.parse import parse
from macrotype.types.resolve import ResolveEnv, resolve


def b(name: str) -> TyType:
    if name == "None":
        return TyType(type_=type(None))
    return TyType(type_=getattr(builtins, name))


# A tiny user generic to exercise qualification/no-op paths
T = t.TypeVar("T")


class Box(t.Generic[T]):  # noqa: D401
    """Test generic."""

    pass


class User:
    pass


# ----- resolution environment -----
ENV = ResolveEnv(
    module="mymod.test",
    imports={
        "User": User,
        "Box": Box,  # allow qualifying bare 'Box' if it ever appears
    },
)


# ----- table: (source annotation object -> expected Resolved Ty) -----
CASES: list[tuple[object, Ty]] = [
    # 1) Forward ref as string
    ("User", TyType(type_=User)),
    # 2) list["User"] → list[pkg.models.User]
    (
        list["User"],  # noqa: F821
        TyApp(base=b("list"), args=(TyType(type_=User),)),
    ),
    # 3) typing.Type["User"] → type[pkg.models.User]
    (
        t.Type["User"],  # noqa: F821
        TyApp(base=b("type"), args=(TyType(type_=User),)),
    ),
    # 4) No-op on already-qualified user generic
    (
        Box[int],
        TyApp(base=TyType(type_=Box), args=(b("int"),)),
    ),
    # 5) Union containing forward & normal
    (
        t.Union["User", int],  # noqa: F821
        TyUnion(options=(TyType(type_=User), b("int"))),
    ),
    # 6) Callable[..., "User"]
    (
        t.Callable[..., "User"],  # noqa: F821
        TyCallable(params=..., ret=TyType(type_=User)),
    ),
    # 7) dataclasses.InitVar inner resolves
    (
        InitVar["User"],  # noqa: F821
        TyApp(base=TyType(type_=InitVar), args=(TyType(type_=User),)),
    ),
]


def test_resolve_table_driven():
    got = [(src, resolve(parse(src), ENV).ty) for src, _ in CASES]
    assert CASES == got


def test_unresolved_forward_remains():
    # Not in imports map → stays TyForward
    ty = resolve(parse("MissingType"), ENV).ty
    assert isinstance(ty, TyForward) and ty.qualname == "MissingType"

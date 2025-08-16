from __future__ import annotations

import builtins
import typing as t
from dataclasses import InitVar
from types import EllipsisType

import pytest

from macrotype.types.ir import (
    TyApp,
    TyCallable,
    TyLiteral,
    TyParamSpec,
    TyRoot,
    TyType,
    TyTypeVarTuple,
    TyUnion,
    TyUnpack,
)
from macrotype.types.validate import TypeValidationError, validate


def b(name: str) -> TyType:
    if name == "Ellipsis":
        return TyType(type_=EllipsisType)
    if name == "None":
        return TyType(type_=type(None))
    return TyType(type_=getattr(builtins, name))


def typ(name: str) -> TyType:
    return TyType(type_=getattr(t, name))


# -------- GOOD CASES (should pass) --------
GOOD = [
    b("int"),
    TyUnion(options=(b("int"), b("str"))),
    TyLiteral(values=(1, "x", (True, 2))),
    TyApp(base=b("tuple"), args=()),  # tuple[()]
    TyApp(base=b("tuple"), args=(b("int"), b("str"))),
    TyApp(base=b("tuple"), args=(b("int"), b("Ellipsis"))),  # tuple[int, ...]
    TyApp(base=b("tuple"), args=(b("int"), b("str"), b("Ellipsis"))),  # tuple[int, str, ...]
    TyCallable(params=..., ret=b("int")),  # Callable[..., int]
    TyCallable(params=(b("int"), b("str")), ret=b("bool")),  # Callable[[int, str], bool]
    TyCallable(params=(TyParamSpec(name="P"),), ret=b("int")),  # Callable[P, int]
    TyCallable(
        params=(TyApp(base=typ("Concatenate"), args=(b("int"), TyParamSpec(name="P"))),),
        ret=b("int"),
    ),  # Callable[Concatenate[int, P], int]
    TyCallable(
        params=(TyUnpack(inner=TyTypeVarTuple(name="Ts")),),
        ret=b("int"),
    ),  # Callable[[Unpack[Ts]], int]
    TyApp(
        base=b("tuple"),
        args=(TyUnpack(inner=TyTypeVarTuple(name="Ts")),),
    ),  # tuple[Unpack[Ts]]
    TyApp(
        base=b("tuple"),
        args=(b("int"), TyUnpack(inner=TyTypeVarTuple(name="Ts"))),
    ),  # tuple[int, Unpack[Ts]]
    TyApp(
        base=b("tuple"),
        args=(TyUnpack(inner=TyTypeVarTuple(name="Ts")), b("int")),
    ),  # tuple[Unpack[Ts], int]
    TyApp(base=TyType(type_=InitVar), args=(b("int"),)),  # InitVar[int]
]


@pytest.mark.parametrize("node", GOOD)
def test_validate_good(node):
    # treat input as NormalizedTy already
    validate(TyRoot(ty=node))  # should not raise


# -------- BAD CASES (should raise) --------
BAD = [
    TyLiteral(values=(1.0,)),  # float not allowed in Literal
    TyApp(base=b("tuple"), args=(b("Ellipsis"), b("int"))),  # tuple[..., int] invalid
    TyApp(base=b("tuple"), args=(b("int"), b("Ellipsis"), b("str"))),  # Ellipsis not last
    TyApp(base=b("tuple"), args=(b("int"), b("Ellipsis"), b("Ellipsis"))),  # multiple Ellipsis
    TyApp(base=b("tuple"), args=(TyTypeVarTuple(name="Ts"),)),  # tuple[Ts] missing Unpack
    TyUnion(options=()),  # empty Union slipped through
    TyUnpack(inner=TyTypeVarTuple(name="Ts")),  # Unpack outside tuple/Concatenate
]


@pytest.mark.parametrize("node", BAD)
def test_validate_bad(node):
    with pytest.raises(TypeValidationError):
        validate(TyRoot(ty=node))

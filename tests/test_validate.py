from __future__ import annotations

import pytest

from macrotype.types_ir import (
    TyApp,
    TyCallable,
    TyLiteral,
    TyName,
    TyParamSpec,
    TyTuple,
    TyTypeVarTuple,
    TyUnion,
    TyUnpack,
)
from macrotype.validate import TypeValidationError, validate


def b(name: str) -> TyName:
    return TyName(module="builtins", name=name)


def typ(name: str) -> TyName:
    return TyName(module="typing", name=name)


# -------- GOOD CASES (should pass) --------
GOOD = [
    b("int"),
    TyUnion(options=(b("int"), b("str"))),
    TyLiteral(values=(1, "x", (True, 2))),
    TyTuple(items=(b("int"), b("str"))),
    TyApp(base=b("tuple"), args=(b("int"), b("Ellipsis"))),  # tuple[int, ...]
    TyApp(base=b("tuple"), args=(b("int"), b("str"), b("Ellipsis"))),  # tuple[int, str, ...]
    TyCallable(params=..., ret=b("int")),  # Callable[..., int]
    TyCallable(params=(b("int"), b("str")), ret=b("bool")),  # Callable[[int, str], bool]
    TyCallable(params=(TyParamSpec(name="P"),), ret=b("int")),  # Callable[P, int]
    TyCallable(
        params=(TyApp(base=typ("Concatenate"), args=(b("int"), TyParamSpec(name="P"))),),
        ret=b("int"),
    ),  # Callable[Concatenate[int, P], int]
    TyTuple(items=(TyUnpack(inner=TyTypeVarTuple(name="Ts")),)),  # tuple[Unpack[Ts]]
]


@pytest.mark.parametrize("node", GOOD)
def test_validate_good(node):
    # treat input as NormalizedTy already
    validate(node)  # should not raise


# -------- BAD CASES (should raise) --------
BAD = [
    TyLiteral(values=(1.0,)),  # float not allowed in Literal
    TyApp(base=b("tuple"), args=(b("Ellipsis"), b("int"))),  # tuple[..., int] invalid
    TyApp(base=b("tuple"), args=(b("int"), b("Ellipsis"), b("str"))),  # Ellipsis not last
    TyApp(base=b("tuple"), args=(b("int"), b("Ellipsis"), b("Ellipsis"))),  # multiple Ellipsis
    TyUnion(options=()),  # empty Union slipped through
    TyUnpack(inner=TyTypeVarTuple(name="Ts")),  # Unpack outside tuple/Concatenate
]


@pytest.mark.parametrize("node", BAD)
def test_validate_bad(node):
    with pytest.raises(TypeValidationError):
        validate(node)

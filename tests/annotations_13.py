# from https://docs.python.org/3.13/reference/compound_stmts.html#type-params
from typing import Callable

def overly_generic[
    SimpleTypeVar,
    TypeVarWithBound: int,
    TypeVarWithConstraints: (str, bytes),
    TypeVarWithDefault = int,
    *SimpleTypeVarTuple = (int, float),
    **SimpleParamSpec = (str, bytearray),
](
    a: SimpleTypeVar,
    b: TypeVarWithDefault,
    c: TypeVarWithBound,
    d: Callable[SimpleParamSpec, TypeVarWithConstraints],
    *e: SimpleTypeVarTuple,
) -> None:
    ...

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

# Edge case: alias with a default type parameter
type DefaultList[T = int] = list[T]

# Edge case: class with a default type parameter
class DefaultBox[T = int]:
    value: T

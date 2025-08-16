from typing import Callable, Concatenate, ParamSpec

from macrotype.meta_types import overload_for

# Function using ParamSpecArgs and ParamSpecKwargs
P = ParamSpec("P")


def with_paramspec_args_kwargs(fn: Callable[P, int], *args: P.args, **kwargs: P.kwargs) -> int: ...


# Wrapper function using ``Concatenate`` with a ``ParamSpec`` parameter
def prepend_one(fn: Callable[Concatenate[int, P], int]) -> Callable[P, int]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> int:
        return fn(1, *args, **kwargs)

    return inner


@overload_for(0)
@overload_for(1)
def special_neg(val: int) -> int:
    match val:
        case 0:
            return 0
        case 1:
            return -1
        case _:
            return -val


@overload_for(val=None)
def parse_int_or_none(val: str | None) -> int | None:
    if val is None:
        return None
    return int(val)

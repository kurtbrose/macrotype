from typing import Callable, Concatenate, ParamSpec

# Function using ParamSpecArgs and ParamSpecKwargs
P = ParamSpec("P")


def with_paramspec_args_kwargs(fn: Callable[P, int], *args: P.args, **kwargs: P.kwargs) -> int: ...


# Wrapper function using ``Concatenate`` with a ``ParamSpec`` parameter
def prepend_one(fn: Callable[Concatenate[int, P], int]) -> Callable[P, int]:
    def inner(*args: P.args, **kwargs: P.kwargs) -> int:
        return fn(1, *args, **kwargs)

    return inner

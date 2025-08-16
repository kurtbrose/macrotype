from typing import Callable, ParamSpec

# Function using ParamSpecArgs and ParamSpecKwargs
P = ParamSpec("P")


def with_paramspec_args_kwargs(fn: Callable[P, int], *args: P.args, **kwargs: P.kwargs) -> int: ...

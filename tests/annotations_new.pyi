# Generated via: macrotype tests/annotations_new.py -o tests/annotations_new.pyi
# Do not edit by hand
from typing import Callable, ParamSpec

P = ParamSpec("P")

def with_paramspec_args_kwargs[**P](
    fn: Callable[P, int], *args: P.args, **kwargs: P.kwargs
) -> int: ...

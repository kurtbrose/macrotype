# Generated via: macrotype tests/annotations_new.py --modules -o tests/annotations_new.pyi
# Do not edit by hand
from typing import Any, Callable, Concatenate, Final, Literal, ParamSpec, overload

P = ParamSpec("P")

def with_paramspec_args_kwargs[**P](fn: Callable[P, int], *args: P.args, **kwargs: P.kwargs) -> int: ...

def prepend_one[**P](fn: Callable[Concatenate[int, P], int]) -> Callable[P, int]: ...

@overload
def special_neg(val: Literal[0]) -> Literal[0]: ...

@overload
def special_neg(val: Literal[1]) -> Literal[-1]: ...

@overload
def special_neg(val: int) -> int: ...

@overload
def parse_int_or_none(val: None) -> None: ...

@overload
def parse_int_or_none(val: None | str) -> None | int: ...

GLOBAL: int

CONST: Final[str]

ANY_VAR: Any

FUNC_ELLIPSIS: Callable[..., int]

TUPLE_UNANN: tuple

TUPLE_EMPTY: tuple[()]

TUPLE_ONE: tuple[int]

TUPLE_VAR: tuple[int, ...]

SET_VAR: set[int]

FROZENSET_VAR: frozenset[str]

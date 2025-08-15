import typing as t

import pytest

from macrotype.types import from_type, unparse_top


@pytest.mark.parametrize(
    "tp",
    [tuple, tuple[()], tuple[int], tuple[int, ...]],
)
def test_tuple_roundtrip(tp):
    assert unparse_top(from_type(tp)) == tp


def test_callable_paramspec_roundtrip():
    P = t.ParamSpec("P")
    ann = t.Callable[P, int]
    assert repr(unparse_top(from_type(ann))) == repr(ann)


def test_callable_concatenate_roundtrip():
    P = t.ParamSpec("P")
    ann = t.Callable[t.Concatenate[int, P], int]
    assert repr(unparse_top(from_type(ann))) == repr(ann)

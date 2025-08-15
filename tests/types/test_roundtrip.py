import pytest

from macrotype.types import from_type, unparse_top


@pytest.mark.parametrize(
    "tp",
    [tuple, tuple[()], tuple[int], tuple[int, ...]],
)
def test_tuple_roundtrip(tp):
    assert unparse_top(from_type(tp)) == tp

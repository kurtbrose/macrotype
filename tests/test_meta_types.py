import typing

from macrotype.meta_types import clear_registry, get_overloads, overload, patch_typing


def test_patch_typing_updates_typing_registry():
    with patch_typing():

        @overload
        def local(x: int) -> int: ...
        def local(x: int) -> int:
            return x

    assert typing.get_overloads(local) == get_overloads(local)

    clear_registry()
    assert typing.get_overloads(local) == []
    assert get_overloads(local) == []

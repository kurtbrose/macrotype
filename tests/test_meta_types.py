import typing

from macrotype.meta_types import (
    clear_registry,
    get_overloads,
    optional,
    overload,
    patch_typing,
    required,
)


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


def test_optional_required_custom_null():
    class Undefined: ...

    class Cls:
        a: int
        b: str | Undefined

    OptCls = optional("OptCls", Cls, null=Undefined)
    ReqCls = required("ReqCls", Cls, null=Undefined)

    assert OptCls.__annotations__ == {"a": int | Undefined, "b": str | Undefined}
    assert ReqCls.__annotations__ == {"a": int, "b": str}

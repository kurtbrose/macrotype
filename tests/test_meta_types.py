import typing

from macrotype.meta_types import (
    clear_registry,
    final,
    get_overloads,
    omit,
    optional,
    overload,
    patch_typing,
    pick,
    replace,
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


def test_meta_type_functions_include_bases():
    class Base:
        x: int

    class Child(Base):
        y: str

    Opt = optional("Opt", Child)
    Req = required("Req", Child)
    Pik = pick("Pik", Child, ["x", "y"])
    Om = omit("Om", Child, ["y"])
    Fin = final("Fin", Child)
    Rep = replace("Rep", Child, {"z": float})

    assert Opt.__annotations__ == {"x": int | None, "y": str | None}
    assert Req.__annotations__ == {"x": int, "y": str}
    assert Pik.__annotations__ == {"x": int, "y": str}
    assert Om.__annotations__ == {"x": int}
    assert Fin.__annotations__ == {"x": typing.Final[int], "y": typing.Final[str]}
    assert Rep.__annotations__ == {"x": int, "y": str, "z": float}


def test_optional_required_custom_null():
    class Undefined: ...

    class Cls:
        a: int
        b: str | Undefined

    OptCls = optional("OptCls", Cls, null=Undefined)
    ReqCls = required("ReqCls", Cls, null=Undefined)

    assert OptCls.__annotations__ == {"a": int | Undefined, "b": str | Undefined}
    assert ReqCls.__annotations__ == {"a": int, "b": str}

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

    Opt = optional(Child)
    Req = required(Child)
    Pik = pick(Child, ["x", "y"])
    Om = omit(Child, ["y"])
    Fin = final(Child)
    Rep = replace("Rep", Child, {"z": float})

    assert Opt == {"x": int | None, "y": str | None}
    assert Req == {"x": int, "y": str}
    assert Pik == {"x": int, "y": str}
    assert Om == {"x": int}
    assert Fin == {"x": typing.Final[int], "y": typing.Final[str]}
    assert Rep.__annotations__ == {"x": int, "y": str, "z": float}


def test_optional_required_custom_null():
    class Undefined: ...

    class Cls:
        a: int
        b: str | Undefined

    OptCls = optional(Cls, null=Undefined)
    ReqCls = required(Cls, null=Undefined)

    assert OptCls == {"a": int | Undefined, "b": str | Undefined}
    assert ReqCls == {"a": int, "b": str}

from __future__ import annotations

import enum
import typing as t

from macrotype.parse_type import to_ir
from macrotype.types_ir import (
    Ty,
    TyAnnotated,
    TyApp,
    TyCallable,
    TyClassVar,
    TyForward,
    TyLiteral,
    TyName,
    TyTuple,
    TyUnion,
)


class Color(enum.Enum):
    RED = 1


# handy shorthands
def b(name: str) -> TyName:
    return TyName(module="builtins", name=name)


def typ(name: str) -> TyName:
    return TyName(module="typing", name=name)


CASES: list[tuple[object, Ty]] = [
    # --- Union / Optional ---
    (int | None, TyUnion(options=(b("int"), b("None")))),
    # --- Annotated (metadata opaque) ---
    (
        t.Annotated[int, "ms", {"unit": "ms"}],
        TyAnnotated(base=b("int"), anno=("ms", {"unit": "ms"})),
    ),
    # --- Literal (PEP 586 shapes) ---
    (t.Literal[1, "x", (True, 2), Color.RED], TyLiteral(values=(1, "x", (True, 2), Color.RED))),
    # --- Builtin generics ---
    (list[int], TyApp(base=b("list"), args=(b("int"),))),
    (dict[str, bool], TyApp(base=b("dict"), args=(b("str"), b("bool")))),
    # --- Tuple fixed vs variadic ---
    (tuple[int, str], TyTuple(items=(b("int"), b("str")))),
    (tuple[int, ...], TyApp(base=b("tuple"), args=(b("int"), b("Ellipsis")))),
    # --- Callable forms ---
    (t.Callable[[int, str], bool], TyCallable(params=(b("int"), b("str")), ret=b("bool"))),
    (t.Callable[..., int], TyCallable(params=..., ret=b("int"))),
    # --- ClassVar, Final/Required unwrap at type level ---
    (t.ClassVar[int], TyClassVar(inner=b("int"))),
    (t.Final[int], b("int")),
    (t.Required[int], b("int")),
    (t.NotRequired[str], b("str")),
    # --- ForwardRef (string) ---
    ("User", TyForward(qualname="User")),
    # --- typing.Type / builtins.type ---
    (t.Type[int], TyApp(base=b("type"), args=(b("int"),))),
]


def test_parse_table_driven():
    for src, expected in CASES:
        got = to_ir(src)
        assert got == expected, f"\nSRC: {src!r}\nGOT: {got!r}\nEXP: {expected!r}"


def test_user_generic_application():
    T = t.TypeVar("T")

    class Box(t.Generic[T]): ...

    # Box[int] → TyApp(TyName("...","Box"), (builtins.int,))
    got = to_ir(Box[int])
    assert isinstance(got, TyApp)
    assert isinstance(got.base, TyName) and got.base.name.endswith("Box")
    assert got.args == (b("int"),)

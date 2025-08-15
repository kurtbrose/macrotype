from __future__ import annotations

import pathlib
import typing as t
from dataclasses import InitVar
from types import ModuleType
from typing import (
    Annotated,
    Any,
    Callable,
    ClassVar,
    Literal,
    NewType,
    ParamSpec,
    TypeAliasType,
    Union,
)

from macrotype.meta_types import set_module
from macrotype.modules import resolve_imports
from macrotype.modules.emit import (
    build_name_map,
    emit_module,
    flatten_annotation_atoms,
    stringify_annotation,
)
from macrotype.modules.ir import (
    ClassDecl,
    FuncDecl,
    ModuleDecl,
    Site,
    TypeDefDecl,
    VarDecl,
)

# ---- table: ModuleDecl -> emitted lines ----
mod1 = ModuleType("m1")
case1 = (
    ModuleDecl(
        name=mod1.__name__,
        obj=mod1,
        members=[
            VarDecl(name="x", site=Site(role="var", annotation=Any)),
        ],
    ),
    ["from typing import Any", "", "x: Any"],
)

mod2 = ModuleType("m2")
case2 = (
    ModuleDecl(
        name=mod2.__name__,
        obj=mod2,
        members=[
            VarDecl(name="v", site=Site(role="var", annotation=Any)),
            TypeDefDecl(
                name="Alias",
                value=Site(role="alias_value", annotation=list[int]),
                obj_type=TypeAliasType("Alias", list[int]),
            ),
            FuncDecl(
                name="f",
                params=(Site(role="param", name="x", annotation=int),),
                ret=Site(role="return", annotation=str),
            ),
            ClassDecl(
                name="C",
                bases=(),
                members=(
                    VarDecl(
                        name="y",
                        site=Site(role="var", name="y", annotation=ClassVar[int]),
                    ),
                ),
            ),
        ],
    ),
    [
        "from typing import Any, ClassVar",
        "",
        "v: Any",
        "",
        "type Alias = list[int]",
        "",
        "def f(x: int) -> str: ...",
        "",
        "class C:",
        "    y: ClassVar[int]",
    ],
)

mod3 = ModuleType("m3")
case3 = (
    ModuleDecl(
        name=mod3.__name__,
        obj=mod3,
        members=[
            VarDecl(name="lit", site=Site(role="var", annotation=Literal["hi"])),
        ],
    ),
    ["from typing import Literal", "", "lit: Literal['hi']"],
)

mod4 = ModuleType("m4")
case4 = (
    ModuleDecl(
        name=mod4.__name__,
        obj=mod4,
        members=[
            VarDecl(
                name="cb1",
                site=Site(role="var", annotation=Callable[[int, str], bool]),
            ),
            VarDecl(
                name="cb2",
                site=Site(role="var", annotation=Callable[..., int]),
            ),
            VarDecl(
                name="nested",
                site=Site(role="var", annotation=list[Callable[[int], str]]),
            ),
            VarDecl(
                name="combo",
                site=Site(
                    role="var",
                    annotation=Callable[[int], str] | Callable[..., bool],
                ),
            ),
        ],
    ),
    [
        "from typing import Callable, Union",
        "",
        "cb1: Callable[[int, str], bool]",
        "",
        "cb2: Callable[..., int]",
        "",
        "nested: list[Callable[[int], str]]",
        "",
        "combo: Union[Callable[[int], str], Callable[..., bool]]",
    ],
)

mod5 = ModuleType("m5")
case5 = (
    ModuleDecl(
        name=mod4.__name__,
        obj=mod4,
        members=[
            VarDecl(
                name="ann",
                site=Site(role="var", annotation=Annotated[int, "meta"]),
            ),
        ],
    ),
    ["from typing import Annotated", "", "ann: Annotated[int, 'meta']"],
)

mod6 = ModuleType("m6")
case6 = (
    ModuleDecl(
        name=mod5.__name__,
        obj=mod5,
        members=[
            VarDecl(
                name="nested",
                site=Site(
                    role="var",
                    annotation=Annotated[Annotated[int, "inner"], "outer"],
                ),
            ),
        ],
    ),
    [
        "from typing import Annotated",
        "",
        "nested: Annotated[int, 'inner', 'outer']",
    ],
)

mod7 = ModuleType("m7")
case7 = (
    ModuleDecl(
        name=mod7.__name__,
        obj=mod7,
        members=[
            VarDecl(name="u", site=Site(role="var", annotation=Union[int, str])),
            VarDecl(name="s", site=Site(role="var", annotation="A")),
        ],
    ),
    [
        "from typing import Union",
        "",
        "u: Union[int, str]",
        "",
        "s: 'A'",
    ],
)
mod8 = ModuleType("m8")
case8 = (
    ModuleDecl(
        name=mod8.__name__,
        obj=mod8,
        members=[
            TypeDefDecl(
                name="UserId",
                value=Site(role="alias_value", annotation=int),
                obj_type=NewType,
            ),
        ],
    ),
    ["from typing import NewType", "", 'UserId = NewType("UserId", int)'],
)

mod9 = ModuleType("m9")
case9 = (
    ModuleDecl(
        name=mod9.__name__,
        obj=mod9,
        members=[
            ClassDecl(name="P", bases=(), members=(), decorators=("runtime_checkable",)),
        ],
    ),
    [
        "from typing import runtime_checkable",
        "",
        "@runtime_checkable",
        "class P:",
        "    ...",
    ],
)


def test_paramspec_unpacked_in_generic():
    P = ParamSpec("P")
    ann1 = tuple[t.Unpack[P.args]]
    nm1 = build_name_map(flatten_annotation_atoms(ann1), locals())
    assert stringify_annotation(ann1, nm1) == "tuple[*P.args]"

    ann2 = Callable[[t.Unpack[P.args], t.Unpack[P.kwargs]], int]
    nm2 = build_name_map(flatten_annotation_atoms(ann2), locals())
    assert stringify_annotation(ann2, nm2) == "Callable[[*P.args, **P.kwargs], int]"


mod10 = ModuleType("m10")
orig = pathlib.Path.__module__
set_module(pathlib.Path, "pathlib._local")
case10 = (
    ModuleDecl(
        name=mod10.__name__,
        obj=mod10,
        members=[
            VarDecl(name="p", site=Site(role="var", annotation=pathlib.Path)),
        ],
    ),
    ["from pathlib import Path", "", "p: Path"],
)
set_module(pathlib.Path, orig)

mod11 = ModuleType("m11")
case11 = (
    ModuleDecl(
        name=mod11.__name__,
        obj=mod11,
        members=[
            VarDecl(
                name="iv",
                site=Site(role="var", annotation=InitVar[list[int]]),
            ),
        ],
    ),
    ["from dataclasses import InitVar", "", "iv: InitVar[list[int]]"],
)


mod12 = ModuleType("m12")
MetaObj = type("MetaObj", (), {"__module__": mod12.__name__, "__repr__": lambda self: "MetaObj()"})
meta_obj = MetaObj()
case12 = (
    ModuleDecl(
        name=mod12.__name__,
        obj=mod12,
        members=[
            VarDecl(
                name="ann_obj",
                site=Site(role="var", annotation=Annotated[int, meta_obj]),
            ),
        ],
    ),
    ["from typing import Annotated", "", "ann_obj: Annotated[int, MetaObj()]"],
)

mod13 = ModuleType("m13")
mod13.NONE_ALIAS = None
case13 = (
    ModuleDecl(
        name=mod13.__name__,
        obj=mod13,
        members=[
            VarDecl(
                name="x",
                site=Site(role="var", annotation=mod13.NONE_ALIAS),
            ),
        ],
    ),
    ["x: None"],
)
CASES = [
    case1,
    case2,
    case3,
    case4,
    case5,
    case6,
    case7,
    case8,
    case9,
    case10,
    case11,
    case12,
    case13,
]


def test_emit_module_table() -> None:
    for mi, _ in CASES:
        resolve_imports(mi)
    got = [emit_module(mi) for mi, _ in CASES]
    expected = [exp for _, exp in CASES]
    assert got == expected

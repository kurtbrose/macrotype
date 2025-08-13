from __future__ import annotations

from types import ModuleType
from typing import Annotated, Any, ClassVar, Literal

from macrotype.modules.emit import emit_module
from macrotype.modules.scanner import ModuleInfo
from macrotype.modules.symbols import AliasSymbol, ClassSymbol, FuncSymbol, Site, VarSymbol

# ---- table: ModuleInfo -> emitted lines ----
mod1 = ModuleType("m1")
case1 = (
    ModuleInfo(
        mod=mod1,
        symbols=[
            VarSymbol(name="x", site=Site(role="var", annotation=Any)),
        ],
    ),
    ["from typing import Any", "", "x: Any"],
)

mod2 = ModuleType("m2")
case2 = (
    ModuleInfo(
        mod=mod2,
        symbols=[
            VarSymbol(name="v", site=Site(role="var", annotation=Any)),
            AliasSymbol(
                name="Alias",
                value=Site(role="alias_value", annotation=list[int]),
            ),
            FuncSymbol(
                name="f",
                params=(Site(role="param", name="x", annotation=int),),
                ret=Site(role="return", annotation=str),
            ),
            ClassSymbol(
                name="C",
                bases=(),
                members=(
                    VarSymbol(
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
    ModuleInfo(
        mod=mod3,
        symbols=[
            VarSymbol(name="lit", site=Site(role="var", annotation=Literal["hi"])),
        ],
    ),
    ["from typing import Literal", "", "lit: Literal['hi']"],
)
mod4 = ModuleType("m4")
case4 = (
    ModuleInfo(
        mod=mod4,
        symbols=[
            VarSymbol(
                name="ann",
                site=Site(role="var", annotation=Annotated[int, "meta"]),
            ),
        ],
    ),
    ["from typing import Annotated", "", "ann: Annotated[int, 'meta']"],
)

mod5 = ModuleType("m5")
case5 = (
    ModuleInfo(
        mod=mod5,
        symbols=[
            VarSymbol(
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

CASES = [case1, case2, case3, case4, case5]


def test_emit_module_table() -> None:
    got = [emit_module(mi) for mi, _ in CASES]
    expected = [exp for _, exp in CASES]
    assert got == expected

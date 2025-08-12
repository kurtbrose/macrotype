from __future__ import annotations

from types import ModuleType

from macrotype.emit_module import emit_module
from macrotype.scanner import ModuleInfo
from macrotype.types.ir import TyAny, TyApp, TyClassVar, TyName
from macrotype.types.symbols import AliasSymbol, ClassSymbol, FuncSymbol, Site, VarSymbol


def b(name: str) -> TyName:  # builtins helper
    return TyName(module="builtins", name=name)


# ---- table: ModuleInfo -> emitted lines ----
mod1 = ModuleType("m1")
case1 = (
    ModuleInfo(
        mod=mod1,
        provenance="m1",
        symbols=[
            VarSymbol(name="x", key="m1.x", site=Site(role="var", raw=None, ty=TyAny())),
        ],
    ),
    ["from typing import Any", "", "x: Any"],
)

mod2 = ModuleType("m2")
case2 = (
    ModuleInfo(
        mod=mod2,
        provenance="m2",
        symbols=[
            VarSymbol(name="v", key="m2.v", site=Site(role="var", raw=None, ty=TyAny())),
            AliasSymbol(
                name="Alias",
                key="m2.Alias",
                value=Site(
                    role="alias_value",
                    raw=None,
                    ty=TyApp(base=b("list"), args=(b("int"),)),
                ),
            ),
            FuncSymbol(
                name="f",
                key="m2.f",
                params=(Site(role="param", name="x", raw=None, ty=b("int")),),
                ret=Site(role="return", raw=None, ty=b("str")),
            ),
            ClassSymbol(
                name="C",
                key="m2.C",
                bases=(),
                members=(
                    VarSymbol(
                        name="y",
                        key="m2.C.y",
                        site=Site(
                            role="var",
                            name="y",
                            raw=None,
                            ty=TyClassVar(inner=b("int")),
                        ),
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

CASES = [case1, case2]


def test_emit_module_table() -> None:
    got = [emit_module(mi) for mi, _ in CASES]
    expected = [exp for _, exp in CASES]
    assert got == expected

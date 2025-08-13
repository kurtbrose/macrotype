from __future__ import annotations

from types import ModuleType
from typing import ClassVar, Required

import pytest

from macrotype.modules import from_module
from macrotype.modules.validate import ModuleValidationError


def test_classvar_only_inside_class() -> None:
    mod = ModuleType("m_classvar")
    mod.__annotations__ = {"x": ClassVar[int]}
    with pytest.raises(ModuleValidationError):
        from_module(mod)


def test_required_only_in_typed_dict() -> None:
    mod = ModuleType("m_required")
    mod.__annotations__ = {"x": Required[int]}
    with pytest.raises(ModuleValidationError):
        from_module(mod)


def test_valid_typed_dict_required() -> None:
    mod = ModuleType("m_td")
    code = (
        "from typing import TypedDict, NotRequired, Required\n"
        "class TD(TypedDict):\n"
        "    a: int\n"
        "    b: NotRequired[int]\n"
        "    c: Required[int]\n"
    )
    exec(code, mod.__dict__)
    import typing

    mod.TD.__annotations__["b"] = typing.NotRequired[int]
    mod.TD.__annotations__["c"] = typing.Required[int]
    mi = from_module(mod)
    from macrotype.modules.symbols import ClassSymbol

    td = next(s for s in mi.symbols if isinstance(s, ClassSymbol) and s.name == "TD")
    assert [f.name for f in td.td_fields] == ["a", "b", "c"]
    assert td.td_fields[1].ty.is_required is False
    assert td.td_fields[2].ty.is_required is True

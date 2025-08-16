from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Annotated

from macrotype.meta_types import emit_as, set_module
from macrotype.modules import emit_module, from_module
from macrotype.stubgen import load_module_from_path


def test_emit_annotations_enums() -> None:
    ann = import_module("tests.annotations_new")
    mi = from_module(ann)
    lines = emit_module(mi)

    assert "from enum import Enum, IntEnum, IntFlag" in lines

    idx = lines.index("class Color(Enum):")
    assert lines[idx + 1] == "    RED = 1"
    assert lines[idx + 2] == "    GREEN = 2"

    idx = lines.index("class Priority(IntEnum):")
    assert lines[idx + 1] == "    LOW = 1"
    assert lines[idx + 2] == "    MEDIUM = 2"
    assert lines[idx + 3] == "    HIGH = 3"

    idx = lines.index("class Permission(IntFlag):")
    assert lines[idx + 1] == "    READ = 1"
    assert lines[idx + 2] == "    WRITE = 2"
    assert lines[idx + 3] == "    EXECUTE = 4"

    idx = lines.index("class StrEnum(str, Enum):")
    assert lines[idx + 1] == "    A = 'a'"
    assert lines[idx + 2] == "    B = 'b'"

    idx = lines.index("class PointEnum(Enum):")
    assert lines[idx + 1] == "    INLINE = Point"
    assert lines[idx + 2] == "    REF = Point"


def test_emit_annotations_headers_and_imports() -> None:
    path = Path(__file__).resolve().parent.parent / "annotations.py"
    ann = load_module_from_path(path)
    mi = from_module(ann)
    lines = emit_module(mi)

    assert lines[0] == "# pyright: basic"
    assert lines[1] == "# mypy: allow-any-expr"
    expected_imports = [
        "from abc import ABC, abstractmethod",
        "from collections.abc import AsyncIterator, Iterator, Sequence",
        "from functools import cached_property",
    ]
    assert lines[2:5] == expected_imports


def test_emit_annotations_inline_meta() -> None:
    mod = ModuleType("m")
    mod.__file__ = __file__

    @emit_as("InlineMeta")
    class Inner:
        pass

    set_module(Inner, "tests.factory")

    mod.InlineMeta = Inner
    mod.__annotations__ = {"x": Annotated[int, Inner]}
    mod.x = 1

    mi = from_module(mod)
    lines = emit_module(mi)
    assert "x: Annotated[int, InlineMeta]" in lines

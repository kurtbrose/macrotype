from importlib import import_module

from macrotype.modules import emit_module, from_module


def test_emit_annotations_enums() -> None:
    ann = import_module("tests.annotations")
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
    assert lines[idx + 1] == "    INLINE = Point(x=1, y=2)"
    assert lines[idx + 2] == "    REF = ORIGIN"

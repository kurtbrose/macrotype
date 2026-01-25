from pathlib import Path

from macrotype.annotate import annotated_code
from macrotype.modules.source import extract_source_info
from macrotype.stubgen import load_module


def test_annotated_copy_replaces_string_annotations() -> None:
    path = Path(__file__).with_name("annotated_copy_sample.py")
    code = path.read_text()
    mod = load_module("tests.annotated_copy_sample", allow_type_checking=True)
    info = extract_source_info(code, allow_type_checking=True)
    updated = annotated_code(mod, source_info=info, strict=True)

    assert '"int"' not in updated
    assert '"Iterable[int]"' not in updated
    assert "value: int" in updated
    assert "def quoted_param(value: int) -> str:" in updated
    assert "def wrap(self, items: Iterable[int]) -> list[int]:" in updated

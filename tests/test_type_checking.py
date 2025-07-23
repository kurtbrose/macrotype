from pathlib import Path

from macrotype.stubgen import load_module_from_path, stub_lines


def test_if_type_checking_overrides():
    mod = load_module_from_path(Path(__file__).with_name("typechecking.py"), type_checking=True)
    lines = stub_lines(mod)
    expected = Path(__file__).with_name("typechecking.pyi").read_text().splitlines()
    assert lines == expected


def test_circular_type_checking_imports():
    base = Path(__file__)
    mod_b = load_module_from_path(base.with_name("circ_b.py"), type_checking=True, module_name="tests.circ_b")
    mod_a = load_module_from_path(base.with_name("circ_a.py"), type_checking=True, module_name="tests.circ_a")

    lines = stub_lines(mod_a)
    expected = base.with_name("circ_a.pyi").read_text().splitlines()
    assert lines == expected

def test_circular_complex_expr_imports():
    base = Path(__file__)
    mod_b = load_module_from_path(
        base.with_name("circ_expr_b.py"),
        type_checking=True,
        module_name="tests.circ_expr_b",
    )
    mod_a = load_module_from_path(
        base.with_name("circ_expr_a.py"),
        type_checking=True,
        module_name="tests.circ_expr_a",
    )

    lines = stub_lines(mod_a)
    expected = base.with_name("circ_expr_a.pyi").read_text().splitlines()
    assert lines == expected

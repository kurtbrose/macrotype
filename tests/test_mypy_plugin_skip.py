from __future__ import annotations

import sys

import pytest

from macrotype.stubgen import MypyPluginError, process_file


def test_path_heuristic_skips_mypy_plugin(tmp_path):
    pkg = tmp_path / "pkg"
    (pkg / "ext" / "mypy").mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "ext" / "__init__.py").write_text("")
    (pkg / "ext" / "mypy" / "__init__.py").write_text("")
    plugin = pkg / "ext" / "mypy" / "infer.py"
    plugin.write_text("raise AssertionError('should not import')\n")

    with pytest.raises(MypyPluginError):
        process_file(plugin)


def test_import_error_classified_as_mypy_plugin(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    bad = pkg / "plugin.py"
    bad.write_text("raise ImportError('missing ExpandTypeVisitor')\n")

    sys.path.insert(0, str(tmp_path))
    try:
        with pytest.raises(MypyPluginError) as exc:
            process_file(bad)
    finally:
        sys.path.remove(str(tmp_path))

    assert "ExpandTypeVisitor" in str(exc.value)

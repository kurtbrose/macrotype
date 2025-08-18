import macrotype.stubgen as stubgen


def test_load_module_from_path_logs_import_error(tmp_path, capsys):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    src = pkg / "mod.py"
    src.write_text("x = 1\n")

    mod = stubgen.load_module_from_path(src, module_name="nonexistent.mod")
    assert mod.x == 1

    captured = capsys.readouterr()
    assert "Could not import nonexistent.mod" in captured.err

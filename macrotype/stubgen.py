from __future__ import annotations

import ast
import importlib
import shutil
import sys
import typing
from pathlib import Path
from types import ModuleType

from .meta_types import patch_typing
from .modules.source import extract_source_info


def _header_lines(command: str | None) -> list[str]:
    """Return standard header lines for generated stubs."""
    if command:
        return [f"# Generated via: {command}", "# Do not edit by hand"]
    return []


def _guess_module_name(path: Path) -> str | None:
    """Best-effort guess of the importable module name for *path*."""
    parts = [path.stem]
    parent = path.parent
    while (parent / "__init__.py").exists():
        parts.append(parent.name)
        parent = parent.parent
    if len(parts) > 1:
        return ".".join(reversed(parts))
    return None


class _TypeCheckingTransformer(ast.NodeTransformer):
    """Rewrite ``if TYPE_CHECKING`` blocks to execute their body."""

    @staticmethod
    def _contains_type_checking(expr: ast.expr) -> bool:
        """Return ``True`` if ``expr`` references ``TYPE_CHECKING`` anywhere."""

        if isinstance(expr, ast.Name) and expr.id == "TYPE_CHECKING":
            return True
        if (
            isinstance(expr, ast.Attribute)
            and isinstance(expr.value, ast.Name)
            and expr.value.id == "typing"
            and expr.attr == "TYPE_CHECKING"
        ):
            return True

        for child in ast.iter_child_nodes(expr):
            if _TypeCheckingTransformer._contains_type_checking(child):
                return True
        return False

    def visit_If(self, node: ast.If) -> ast.stmt:
        self.generic_visit(node)
        if self._contains_type_checking(node.test):
            # Execute the body and ignore the else branch. Errors while
            # executing the body (e.g. ImportError due to circular imports)
            # are suppressed so stub generation can proceed.
            return ast.Try(
                body=node.body,
                handlers=[
                    ast.ExceptHandler(
                        type=ast.Name("Exception", ast.Load()),
                        name=None,
                        body=[ast.Pass()],
                    )
                ],
                orelse=[],
                finalbody=[],
            )
        return node


from .pyi_extract import PyiModule


def _exec_with_type_checking(code: str, module: ModuleType) -> None:
    """Execute *code* in *module* with ``TYPE_CHECKING`` blocks enabled."""
    tree = ast.parse(code)
    tree = _TypeCheckingTransformer().visit(tree)
    ast.fix_missing_locations(tree)

    module.__dict__["TYPE_CHECKING"] = True
    original = typing.TYPE_CHECKING
    typing.TYPE_CHECKING = True
    try:
        with patch_typing():
            exec(compile(tree, getattr(module, "__file__", "<string>"), "exec"), module.__dict__)
    finally:
        typing.TYPE_CHECKING = original


def load_module_from_path(
    path: Path,
    *,
    type_checking: bool = False,
    module_name: str | None = None,
) -> ModuleType:
    """Load a module from ``path``.

    When ``type_checking`` is ``True`` the module is executed with
    ``TYPE_CHECKING`` blocks enabled and their contents executed.

    ``module_name`` controls the name used in :data:`sys.modules` and defaults
    to ``path.stem``.
    """
    name = module_name or _guess_module_name(path) or path.stem
    if not type_checking and "." in name and name not in sys.modules:
        try:
            with patch_typing():
                module = importlib.import_module(name)
            if getattr(module, "__file__", None) and not hasattr(
                module, "__macrotype_header_pragmas__"
            ):
                header, comments, lines = extract_source_info(Path(module.__file__).read_text())
                module.__macrotype_header_pragmas__ = header
                module.__macrotype_comments__ = comments
                module.__macrotype_line_map__ = lines
            return module
        except ImportError:
            pass

    if name in sys.modules:
        module = sys.modules[name]
        if getattr(module, "__file__", None) and Path(module.__file__).resolve() == path.resolve():
            if not hasattr(module, "__macrotype_header_pragmas__"):
                header, comments, lines = extract_source_info(Path(module.__file__).read_text())
                module.__macrotype_header_pragmas__ = header
                module.__macrotype_comments__ = comments
                module.__macrotype_line_map__ = lines
            return module
        del sys.modules[name]

    if not type_checking:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot import {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        with patch_typing():
            spec.loader.exec_module(module)
        header, comments, lines = extract_source_info(Path(path).read_text())
        module.__macrotype_header_pragmas__ = header
        module.__macrotype_comments__ = comments
        module.__macrotype_line_map__ = lines
        return module

    code = Path(path).read_text()
    module = ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    header, comments, lines = extract_source_info(code)
    module.__macrotype_header_pragmas__ = header
    module.__macrotype_comments__ = comments
    module.__macrotype_line_map__ = lines
    _exec_with_type_checking(code, module)
    return module


def load_module_from_code(
    code: str,
    name: str = "<string>",
    *,
    type_checking: bool = False,
    module_name: str | None = None,
) -> ModuleType:
    name = module_name or name
    module = ModuleType(name)
    header, comments, lines = extract_source_info(code)
    module.__macrotype_header_pragmas__ = header
    module.__macrotype_comments__ = comments
    module.__macrotype_line_map__ = lines
    if type_checking:
        sys.modules[name] = module
        _exec_with_type_checking(code, module)
    else:
        sys.modules[name] = module
        with patch_typing():
            exec(compile(code, name, "exec"), module.__dict__)
    return module


def stub_lines(module: ModuleType) -> list[str]:
    return PyiModule.from_module(module).render()


def write_stub(dest: Path, lines: list[str], command: str | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(_header_lines(command) + list(lines)) + "\n")


def iter_python_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    files = []
    for p in target.rglob("*.py"):
        if p.name == "__main__.py" and p.parent != target:
            continue
        rel = p.relative_to(target)
        if rel.parts and rel.parts[0] == "test":
            continue
        files.append(p)
    return files


def _link_stub_overlay(src: Path, dest: Path, overlay_dir: Path) -> None:
    module_name = _guess_module_name(src) or src.stem
    parts = module_name.split(".")
    if src.name == "__init__.py":
        overlay = overlay_dir.joinpath(*parts, "__init__.pyi")
    else:
        overlay = overlay_dir.joinpath(*parts[:-1], parts[-1] + ".pyi")
    if overlay.resolve() == dest.resolve():
        return
    overlay.parent.mkdir(parents=True, exist_ok=True)
    try:
        if overlay.exists() or overlay.is_symlink():
            overlay.unlink()
        overlay.symlink_to(dest)
    except OSError:  # pragma: no cover - fallback on systems without symlink
        shutil.copy2(dest, overlay)


def process_file(
    src: Path,
    dest: Path | None = None,
    *,
    command: str | None = None,
    stub_overlay_dir: Path | None = None,
) -> Path:
    module = load_module_from_path(src)
    lines = stub_lines(module)
    dest = dest or src.with_suffix(".pyi")
    write_stub(dest, lines, command)
    if stub_overlay_dir is not None:
        _link_stub_overlay(src, dest, stub_overlay_dir)
    return dest


def process_directory(
    directory: Path,
    out_dir: Path | None = None,
    *,
    command: str | None = None,
    stub_overlay_dir: Path | None = None,
) -> list[Path]:
    outputs = []
    for src in iter_python_files(directory):
        dest = (out_dir / src.with_suffix(".pyi").name) if out_dir else None
        try:
            outputs.append(
                process_file(
                    src,
                    dest,
                    command=command,
                    stub_overlay_dir=stub_overlay_dir,
                )
            )
        except (Exception, SystemExit) as exc:  # pragma: no cover - defensive
            print(f"Skipping {src}: {exc}", file=sys.stderr)
    return outputs


__all__ = [
    "load_module_from_path",
    "load_module_from_code",
    "stub_lines",
    "write_stub",
    "iter_python_files",
    "process_file",
    "process_directory",
]

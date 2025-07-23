from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
import ast
import typing

from .overload_support import patch_typing


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
    name = module_name or path.stem

    if not type_checking:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot import {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        with patch_typing():
            spec.loader.exec_module(module)
        return module

    code = Path(path).read_text()
    module = ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
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


def write_stub(dest: Path, lines: list[str]) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines) + "\n")


def iter_python_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return list(target.rglob("*.py"))


def process_file(src: Path, dest: Path | None = None) -> Path:
    module = load_module_from_path(src)
    lines = stub_lines(module)
    dest = dest or src.with_suffix(".pyi")
    write_stub(dest, lines)
    return dest


def process_directory(directory: Path, out_dir: Path | None = None) -> list[Path]:
    outputs = []
    for src in iter_python_files(directory):
        dest = (out_dir / src.with_suffix(".pyi").name) if out_dir else None
        outputs.append(process_file(src, dest))
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

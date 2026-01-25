from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from . import modules
from .modules.emit import (
    build_name_map,
    collect_all_annotations,
    flatten_annotation_atoms,
    stringify_annotation,
)
from .modules.ir import (
    ClassDecl,
    Decl,
    FuncDecl,
    ModuleDecl,
    Site,
    SourceInfo,
    TypeDefDecl,
    VarDecl,
)
from .modules.source import extract_source_info
from .stubgen import _module_name_from_path, iter_python_files, load_module


@dataclass(frozen=True)
class ScopeIndex:
    vars: dict[str, VarDecl]
    funcs: dict[str, FuncDecl]
    classes: dict[str, ClassDecl]


@dataclass(frozen=True)
class FuncAnnotations:
    params: dict[str, str]
    returns: str | None


def _scope_index(decls: list[Decl]) -> ScopeIndex:
    vars: dict[str, VarDecl] = {}
    funcs: dict[str, FuncDecl] = {}
    classes: dict[str, ClassDecl] = {}

    for decl in decls:
        if isinstance(decl, VarDecl):
            vars[decl.name] = decl
        elif isinstance(decl, FuncDecl):
            existing = funcs.get(decl.name)
            if existing is None or (
                "overload" in existing.decorators and "overload" not in decl.decorators
            ):
                funcs[decl.name] = decl
        elif isinstance(decl, ClassDecl):
            classes[decl.name] = decl
    return ScopeIndex(vars=vars, funcs=funcs, classes=classes)


def _build_name_map(mi: ModuleDecl) -> dict[int, str]:
    annotations = collect_all_annotations(mi)
    atoms: dict[int, object] = {}
    for ann in annotations:
        atoms.update(flatten_annotation_atoms(ann))
    for sym in mi.get_all_decls():
        if isinstance(sym, TypeDefDecl) and sym.value is not None:
            atoms.update(flatten_annotation_atoms(sym.value.annotation))
    return build_name_map(atoms.values(), mi.obj.__dict__)


def _offset_for(line_offsets: list[int], lineno: int, col: int) -> int:
    return line_offsets[lineno - 1] + col


class AnnotationApplier:
    def __init__(
        self,
        code: str,
        *,
        module: ModuleType,
        mi: ModuleDecl,
        name_map: dict[int, str],
    ) -> None:
        self.code = code
        self.module = module
        self.mi = mi
        self.name_map = name_map
        self.lines = code.splitlines(keepends=True)
        self.line_offsets = _line_offsets(self.lines)
        self.replacements: list[tuple[int, int, str]] = []

    def apply(self) -> str:
        tree = self.mi.source.tree if self.mi.source is not None else ast.parse(self.code)
        scope = _scope_index(self.mi.members)
        self._visit_body(tree.body, scope)
        self._insert_imports(tree)
        return _apply_replacements(self.code, self.replacements)

    def _render(self, ann: object) -> str:
        return stringify_annotation(ann, self.name_map, self.module.__name__)

    def _annotation_for_site(self, site: Site) -> str | None:
        if site.annotation is inspect._empty:
            return None
        return self._render(site.annotation)

    def _func_annotations(self, sym: FuncDecl) -> FuncAnnotations:
        params: dict[str, str] = {}
        for site in sym.params:
            name = site.name or ""
            if name in {"*", "/"}:
                continue
            ann = self._annotation_for_site(site)
            if ann is None:
                continue
            params[name.lstrip("*")] = ann
        ret = None
        if sym.ret is not None:
            ret = self._annotation_for_site(sym.ret)
        return FuncAnnotations(params=params, returns=ret)

    def _add_replacement(self, node: ast.AST, text: str) -> None:
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            return
        start = _offset_for(self.line_offsets, node.lineno, node.col_offset)  # type: ignore[arg-type]
        end = _offset_for(
            self.line_offsets,
            node.end_lineno,
            node.end_col_offset,  # type: ignore[arg-type]
        )
        self.replacements.append((start, end, text))

    def _insert_at_node_end(self, node: ast.AST, text: str) -> None:
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            return
        offset = _offset_for(self.line_offsets, node.end_lineno, node.end_col_offset)  # type: ignore[arg-type]
        self.replacements.append((offset, offset, text))

    def _apply_arg(self, arg: ast.arg, annotations: FuncAnnotations) -> None:
        name = arg.arg
        ann = annotations.params.get(name)
        if not ann:
            return
        if arg.annotation is not None:
            self._add_replacement(arg.annotation, ann)
        else:
            self._insert_at_node_end(arg, f": {ann}")

    def _apply_function(self, node: ast.AST, sym: FuncDecl) -> None:
        annotations = self._func_annotations(sym)
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        for arg in node.args.posonlyargs:
            self._apply_arg(arg, annotations)
        for arg in node.args.args:
            self._apply_arg(arg, annotations)
        for arg in node.args.kwonlyargs:
            self._apply_arg(arg, annotations)
        if node.args.vararg is not None:
            self._apply_arg(node.args.vararg, annotations)
        if node.args.kwarg is not None:
            self._apply_arg(node.args.kwarg, annotations)
        if node.returns is not None and annotations.returns is not None:
            self._add_replacement(node.returns, annotations.returns)

    def _apply_var(self, node: ast.AST, var_decl: VarDecl) -> None:
        if not isinstance(node, ast.AnnAssign):
            return
        ann = self._annotation_for_site(var_decl.site)
        if ann is None or node.annotation is None:
            return
        self._add_replacement(node.annotation, ann)

    def _visit_body(self, body: list[ast.stmt], scope: ScopeIndex) -> None:
        for node in body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                var_decl = scope.vars.get(node.target.id)
                if var_decl is not None:
                    self._apply_var(node, var_decl)
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sym = scope.funcs.get(node.name)
                if sym is not None:
                    self._apply_function(node, sym)
                continue
            if isinstance(node, ast.ClassDef):
                cls_decl = scope.classes.get(node.name)
                if cls_decl is None:
                    continue
                class_scope = _scope_index(list(cls_decl.members))
                self._visit_body(node.body, class_scope)

    def _insert_imports(self, tree: ast.Module) -> None:
        if self.mi.imports is None:
            return
        import_lines = self.mi.imports.lines()
        if not import_lines:
            return
        existing_lines = set(self.code.splitlines())
        import_lines = [line for line in import_lines if line not in existing_lines]
        if not import_lines:
            return
        insertion_offset = _import_insertion_offset(tree, self.lines, self.line_offsets)
        block = "\n".join(import_lines) + "\n\n"
        self.replacements.append((insertion_offset, insertion_offset, block))


def _line_offsets(lines: list[str]) -> list[int]:
    offsets: list[int] = []
    total = 0
    for line in lines:
        offsets.append(total)
        total += len(line)
    if not lines:
        offsets.append(0)
    return offsets


def _import_insertion_offset(tree: ast.Module, lines: list[str], line_offsets: list[int]) -> int:
    insert_after: ast.AST | None = None
    body = tree.body
    idx = 0
    if body and isinstance(body[0], ast.Expr):
        value = body[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            insert_after = body[0]
            idx = 1
    for node in body[idx:]:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            insert_after = node
            continue
        break
    if insert_after is None or not hasattr(insert_after, "end_lineno"):
        return 0
    end_line = insert_after.end_lineno  # type: ignore[assignment]
    if end_line is None or end_line - 1 >= len(lines):
        return 0
    return line_offsets[end_line - 1] + len(lines[end_line - 1])


def _apply_replacements(code: str, replacements: list[tuple[int, int, str]]) -> str:
    if not replacements:
        return code
    updated = code
    for start, end, text in sorted(replacements, key=lambda item: item[0], reverse=True):
        updated = updated[:start] + text + updated[end:]
    return updated


def annotated_code(
    module: ModuleType,
    *,
    source_info: SourceInfo | None = None,
    strict: bool = False,
) -> str:
    if source_info is None or source_info.code is None:
        raise ValueError("source_info with code is required to generate annotated copies")
    mi = modules.from_module(module, source_info=source_info, strict=strict)
    name_map = _build_name_map(mi)
    applier = AnnotationApplier(source_info.code, module=module, mi=mi, name_map=name_map)
    return applier.apply()


def write_annotated(dest: Path, code: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(code)


def process_file(
    src: Path,
    dest: Path | None = None,
    *,
    strict: bool = False,
    allow_type_checking: bool = False,
) -> Path:
    code = src.read_text()
    info = extract_source_info(code, allow_type_checking=allow_type_checking)
    module_name = _module_name_from_path(src)
    module = load_module(module_name, allow_type_checking=True)
    dest = dest or src
    annotated = annotated_code(module, source_info=info, strict=strict)
    write_annotated(dest, annotated)
    return dest


def process_directory(
    directory: Path,
    out_dir: Path,
    *,
    strict: bool = False,
    allow_type_checking: bool = False,
    skip: tuple[str, ...] = (),
) -> list[Path]:
    outputs: list[Path] = []
    for src in iter_python_files(directory, skip=skip):
        rel = src.relative_to(directory)
        dest = out_dir / rel
        outputs.append(
            process_file(
                src,
                dest,
                strict=strict,
                allow_type_checking=allow_type_checking,
            )
        )
    return outputs


__all__ = [
    "annotated_code",
    "write_annotated",
    "process_file",
    "process_directory",
]

from __future__ import annotations

import types
from collections.abc import Callable
from typing import Annotated, Any, ForwardRef, Iterable, get_args, get_origin

INDENT = "    "

import typing as t

from .scanner import ModuleInfo
from .symbols import AliasSymbol, ClassSymbol, FuncSymbol, Symbol, VarSymbol


def emit_module(mi: ModuleInfo) -> list[str]:
    """Emit `.pyi` lines for a ModuleInfo using annotations only."""
    annotations = collect_all_annotations(mi)
    atoms: dict[int, Any] = {}
    for ann in annotations:
        atoms.update(flatten_annotation_atoms(ann))

    context = mi.mod.__dict__
    name_map = build_name_map(atoms.values(), context)

    lines: list[str] = []
    for sym in mi.symbols:
        if not sym.emit:
            continue
        lines.extend(_emit_symbol(sym, name_map, indent=0))
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()

    # Collect typing imports
    typing_names = {
        name_map[id(a)]
        for a in atoms.values()
        if getattr(a, "__module__", None) == "typing" or a is Callable
    }
    typing_names.update(_collect_typing_names(mi.symbols))

    pre: list[str] = []
    if typing_names:
        pre.append(f"from typing import {', '.join(sorted(typing_names))}")
        if lines:
            pre.append("")

    return pre + lines


def _collect_typing_names(symbols: Iterable[Symbol]) -> set[str]:
    names: set[str] = set()
    for sym in symbols:
        if not sym.emit:
            continue
        for deco in getattr(sym, "decorators", ()):  # collect decorator names from typing
            base = deco.split("(")[0].split(".")[-1]
            if base in {"final", "override", "overload", "runtime_checkable"}:
                names.add(base)
        match sym:
            case AliasSymbol(alias_type=alias):
                match alias:
                    case t.TypeVar():
                        names.add("TypeVar")
                    case t.ParamSpec():
                        names.add("ParamSpec")
                    case t.TypeVarTuple():
                        names.add("TypeVarTuple")
                    case _ if callable(alias) and hasattr(alias, "__supertype__"):
                        names.add("NewType")
            case ClassSymbol(members=members):
                names.update(_collect_typing_names(members))
    return names


def _add_comment(line: str, comment: str | None) -> str:
    if comment:
        return f"{line}  # {comment}"
    return line


def collect_all_annotations(mi: ModuleInfo) -> list[Any]:
    """Walk ModuleInfo and collect all annotations."""
    annos: list[Any] = []

    def visit(sym: Symbol):
        if not sym.emit:
            return
        match sym:
            case VarSymbol(site=site):
                annos.append(site.annotation)
            case AliasSymbol(value=site):
                annos.append(site.annotation)
            case FuncSymbol(params=params, ret=ret):
                for p in params:
                    annos.append(p.annotation)
                if ret:
                    annos.append(ret.annotation)
            case ClassSymbol(bases=bases, td_fields=fields, members=members):
                for b in bases:
                    annos.append(b.annotation)
                for f in fields:
                    annos.append(f.annotation)
                for m in members:
                    visit(m)

    for s in mi.symbols:
        visit(s)
    return annos


def flatten_annotation_atoms(ann: Any) -> dict[int, Any]:
    """Flatten all atomic components of a type annotation."""
    visited: dict[int, Any] = {}
    atoms: dict[int, Any] = {}
    stack = [ann]

    while stack:
        obj = stack.pop()
        obj_id = id(obj)
        if obj_id in visited:
            continue
        visited[obj_id] = obj

        origin = get_origin(obj)
        args = get_args(obj)

        if isinstance(obj, (list, tuple)) and origin is None:
            stack.extend(obj)
            continue

        if isinstance(obj, ForwardRef):
            atoms[obj_id] = obj
            continue

        if origin:
            atoms[id(origin)] = origin
            stack.extend(args)
        elif isinstance(args, tuple):
            atoms[obj_id] = obj
            stack.extend(args)
        else:
            atoms[obj_id] = obj

    return atoms


def build_name_map(atoms: Iterable[Any], context: dict[str, Any]) -> dict[int, str]:
    """Map annotation atoms to names based on module context."""
    reverse = {id(v): k for k, v in context.items()}
    name_map: dict[int, str] = {}

    for atom in atoms:
        atom_id = id(atom)
        if isinstance(atom, ForwardRef):
            name_map[atom_id] = atom.__forward_arg__
        elif atom_id in reverse:
            name_map[atom_id] = reverse[atom_id]
        elif hasattr(atom, "__name__"):
            name_map[atom_id] = atom.__name__
        else:
            name_map[atom_id] = repr(atom)

    return name_map


def stringify_annotation(ann: Any, name_map: dict[int, str]) -> str:
    """Emit string form of a type annotation."""
    if ann is Ellipsis:
        return "..."

    if isinstance(ann, ForwardRef):
        return ann.__forward_arg__

    if isinstance(ann, str):
        return repr(ann)

    origin = get_origin(ann)
    args = get_args(ann)

    if origin is types.UnionType:
        return " | ".join(stringify_annotation(arg, name_map) for arg in args)

    if origin is Callable:
        if not args:
            return "Callable"
        params, ret = args
        ret_str = stringify_annotation(ret, name_map)
        name = name_map.get(id(origin), "Callable")
        if params is Ellipsis:
            return f"{name}[..., {ret_str}]"
        params_str = ", ".join(stringify_annotation(p, name_map) for p in params)
        return f"{name}[[{params_str}], {ret_str}]"

    if origin is Annotated:
        first, *metas = args
        parts = [stringify_annotation(first, name_map)]
        for meta in metas:
            if isinstance(meta, str):
                parts.append(repr(meta))
            else:
                parts.append(stringify_annotation(meta, name_map))
        return f"Annotated[{', '.join(parts)}]"

    if origin:
        name = name_map.get(id(origin), getattr(origin, "__name__", repr(origin)))
        inner = ", ".join(stringify_annotation(arg, name_map) for arg in args)
        return f"{name}[{inner}]"
    else:
        return name_map.get(id(ann), repr(ann))


def _emit_symbol(sym: Symbol, name_map: dict[int, str], *, indent: int) -> list[str]:
    if not sym.emit:
        return []
    pad = INDENT * indent

    match sym:
        case VarSymbol(site=site):
            ty = stringify_annotation(site.annotation, name_map)
            line = f"{pad}{sym.name}: {ty}"
            line = _add_comment(line, sym.comment or site.comment)
            return [line]

        case AliasSymbol(value=site, type_params=params, alias_type=alias):
            match alias:
                case t.TypeVar():
                    line = f"{pad}{sym.name} = {_stringify_typevar(alias, name_map)}"
                case t.ParamSpec():
                    line = f"{pad}{sym.name} = {_stringify_paramspec(alias)}"
                case t.TypeVarTuple():
                    line = f"{pad}{sym.name} = {_stringify_typevartuple(alias)}"
                case t.TypeAlias:  # type: ignore[misc]
                    ty = stringify_annotation(site.annotation, name_map)
                    line = f"{pad}{sym.name} = {ty}"
                case _ if callable(alias) and hasattr(alias, "__supertype__"):
                    ty = stringify_annotation(site.annotation, name_map)
                    line = f'{pad}{sym.name} = NewType("{sym.name}", {ty})'
                case t.TypeAliasType():  # type: ignore[attr-defined]
                    ty = stringify_annotation(site.annotation, name_map)
                    param_str = f"[{', '.join(params)}]" if params else ""
                    line = f"{pad}type {sym.name}{param_str} = {ty}"
                case _:
                    ty = stringify_annotation(site.annotation, name_map)
                    param_str = f"[{', '.join(params)}]" if params else ""
                    line = f"{pad}type {sym.name}{param_str} = {ty}"
            line = _add_comment(line, sym.comment or site.comment)
            return [line]

        case FuncSymbol(params=params, ret=ret, decorators=decos):
            pieces: list[str] = []
            for d in decos:
                pieces.append(f"{pad}@{d}")
            param_strs = [
                f"{p.name}: {stringify_annotation(p.annotation, name_map)}" for p in params
            ]
            ret_str = f" -> {stringify_annotation(ret.annotation, name_map)}" if ret else ""
            line = f"{pad}def {sym.name}({', '.join(param_strs)}){ret_str}: ..."
            line = _add_comment(line, sym.comment)
            pieces.append(line)
            return pieces

        case ClassSymbol(bases=bases, td_fields=fields, members=members, decorators=decos):
            base_str = ""
            if bases:
                base_str = (
                    f"({', '.join(stringify_annotation(b.annotation, name_map) for b in bases)})"
                )
            lines = [f"{pad}@{d}" for d in decos]
            first = f"{pad}class {sym.name}{base_str}:"
            first = _add_comment(first, sym.comment)
            lines.append(first)
            if fields:
                for f in fields:
                    ty = stringify_annotation(f.annotation, name_map)
                    line = f"{pad}{INDENT}{f.name}: {ty}"
                    line = _add_comment(line, f.comment)
                    lines.append(line)
            if members:
                for m in members:
                    lines.extend(_emit_symbol(m, name_map, indent=indent + 1))
            if not fields and not members:
                lines.append(f"{pad}{INDENT}...")
            return lines

        case _:
            raise NotImplementedError(f"Unsupported symbol: {type(sym).__name__}")


def _stringify_typevar(tv: t.TypeVar, name_map: dict[int, str]) -> str:
    args = [f'"{tv.__name__}"']
    if getattr(tv, "__covariant__", False):
        args.append("covariant=True")
    if getattr(tv, "__contravariant__", False):
        args.append("contravariant=True")
    if getattr(tv, "__infer_variance__", False):
        args.append("infer_variance=True")
    bound = getattr(tv, "__bound__", None)
    if bound is not None:
        args.append(f"bound={stringify_annotation(bound, name_map)}")
    constraints = getattr(tv, "__constraints__", ())
    if constraints:
        args.extend(stringify_annotation(c, name_map) for c in constraints)
    return f"TypeVar({', '.join(args)})"


def _stringify_paramspec(ps: t.ParamSpec) -> str:
    args = [f'"{ps.__name__}"']
    if getattr(ps, "__covariant__", False):
        args.append("covariant=True")
    if getattr(ps, "__contravariant__", False):
        args.append("contravariant=True")
    return f"ParamSpec({', '.join(args)})"


def _stringify_typevartuple(tv: t.TypeVarTuple) -> str:
    return f'TypeVarTuple("{tv.__name__}")'

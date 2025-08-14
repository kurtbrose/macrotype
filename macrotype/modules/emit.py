from __future__ import annotations

import types
from collections import defaultdict
from collections.abc import Callable as ABC_Callable
from typing import Annotated, Any, Callable, ForwardRef, Iterable, get_args, get_origin

INDENT = "    "

import typing as t

from .ir import ClassDecl, Decl, FuncDecl, ModuleDecl, TypeDefDecl, VarDecl

# Mapping of alias module names to their canonical form.
_MODULE_ALIASES: dict[str, str] = {
    "pathlib._local": "pathlib",
    "pathlib._pathlib": "pathlib",
}


def emit_module(mi: ModuleDecl) -> list[str]:
    """Emit `.pyi` lines for a ModuleDecl using annotations only."""
    annotations = collect_all_annotations(mi)
    atoms: dict[int, Any] = {}
    for ann in annotations:
        atoms.update(flatten_annotation_atoms(ann))

    context = mi.obj.__dict__
    name_map = build_name_map(atoms.values(), context)

    # Precompute typing import names for later checks.
    typing_names = {
        name_map[id(a)]
        for a in atoms.values()
        if getattr(a, "__module__", None) == "typing" or a in {Callable, ABC_Callable}
    }
    typing_names.update(_collect_typing_names(mi.members))

    # Collect imports for non-typing external modules.
    external: dict[str, set[str]] = defaultdict(set)
    for atom in atoms.values():
        modname = getattr(atom, "__module__", None)
        name = name_map.get(id(atom))
        if not modname or not name:
            continue
        if name in typing_names:
            continue
        modname = _MODULE_ALIASES.get(modname, modname)
        if modname in {"builtins", "typing", mi.obj.__name__}:
            continue
        external[modname].add(name)

    lines: list[str] = []
    for sym in mi.members:
        if not sym.emit:
            continue
        lines.extend(_emit_decl(sym, name_map, indent=0))
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()

    pre: list[str] = []
    if external:
        for mod, names in sorted(external.items()):
            pre.append(f"from {mod} import {', '.join(sorted(names))}")
        if typing_names:
            pre.append("")
        elif lines:
            pre.append("")
    if typing_names:
        pre.append(f"from typing import {', '.join(sorted(typing_names))}")
        if lines:
            pre.append("")
    return pre + lines


def _collect_typing_names(symbols: Iterable[Decl]) -> set[str]:
    names: set[str] = set()
    for sym in symbols:
        if not sym.emit:
            continue
        for deco in getattr(sym, "decorators", ()):  # collect decorator names from typing
            base = deco.split("(")[0].split(".")[-1]
            if base in {"final", "override", "overload", "runtime_checkable"}:
                names.add(base)
        match sym:
            case TypeDefDecl(obj_type=alias):
                if isinstance(alias, (t.TypeVar, t.ParamSpec, t.TypeVarTuple)):
                    names.add(type(alias).__name__)
                elif alias is t.NewType:
                    names.add(alias.__name__)
            case ClassDecl(members=members):
                names.update(_collect_typing_names(members))
    return names


def _add_comment(line: str, comment: str | None) -> str:
    if comment:
        return f"{line}  # {comment}"
    return line


def collect_all_annotations(mi: ModuleDecl) -> list[Any]:
    """Walk ModuleDecl and collect all annotations."""
    annos: list[Any] = []
    for sym in mi.get_all_decls():
        if not sym.emit:
            continue
        for site in sym.get_annotation_sites():
            annos.append(site.annotation)
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

    from collections.abc import Callable as ABC_Callable

    if origin in {Callable, ABC_Callable}:
        if not args:
            return "Callable"
        if len(args) == 2:
            params, ret = args
            params = params if params is not Ellipsis else [Ellipsis]
        else:
            *params, ret = args
        ret_str = stringify_annotation(ret, name_map)
        name = name_map.get(id(origin), getattr(origin, "__name__", "Callable"))
        if params == [Ellipsis]:
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
        return name_map.get(id(ann), getattr(ann, "__name__", repr(ann)))


def _emit_decl(sym: Decl, name_map: dict[int, str], *, indent: int) -> list[str]:
    if not sym.emit:
        return []
    pad = INDENT * indent

    match sym:
        case VarDecl(site=site):
            ty = stringify_annotation(site.annotation, name_map)
            line = f"{pad}{sym.name}: {ty}"
            line = _add_comment(line, sym.comment or site.comment)
            return [line]

        case TypeDefDecl(value=site, type_params=params, obj_type=alias):
            keyword = param_str = ""
            match alias:
                case t.TypeAliasType():  # type: ignore[attr-defined]
                    keyword = "type "
                    rhs = stringify_annotation(site.annotation, name_map)
                    param_str = f"[{', '.join(params)}]" if params else ""
                case t.TypeVar():
                    rhs = _stringify_typevar(alias, name_map)
                case t.ParamSpec():
                    rhs = _stringify_paramspec(alias)
                case t.TypeVarTuple():
                    rhs = _stringify_typevartuple(alias)
                case t.TypeAlias:  # type: ignore[misc]
                    rhs = stringify_annotation(site.annotation, name_map)
                case t.NewType:
                    ty = stringify_annotation(site.annotation, name_map)
                    rhs = f'NewType("{sym.name}", {ty})'
                case _:
                    raise NotImplementedError(f"Unsupported alias type: {alias!r}")
            line = f"{pad}{keyword}{sym.name}{param_str} = {rhs}"
            line = _add_comment(line, sym.comment or site.comment)
            return [line]

        case FuncDecl(params=params, ret=ret, decorators=decos, type_params=tp):
            pieces: list[str] = []
            for d in decos:
                pieces.append(f"{pad}@{d}")
            param_strs: list[str] = []
            for p in params:
                name = p.name or ""
                if name in {"*", "/"}:
                    param_strs.append(name)
                    continue
                if p.annotation is None:
                    param_strs.append(name)
                else:
                    param_strs.append(f"{name}: {stringify_annotation(p.annotation, name_map)}")
            ret_str = f" -> {stringify_annotation(ret.annotation, name_map)}" if ret else ""
            tp_str = f"[{', '.join(tp)}]" if tp else ""
            line = f"{pad}def {sym.name}{tp_str}({', '.join(param_strs)}){ret_str}: ..."
            line = _add_comment(line, sym.comment)
            pieces.append(line)
            return pieces

        case ClassDecl(
            bases=bases,
            td_fields=fields,
            members=members,
            decorators=decos,
            type_params=tp,
        ):
            base_str = ""
            if bases:
                base_str = (
                    f"({', '.join(stringify_annotation(b.annotation, name_map) for b in bases)})"
                )
            tp_str = f"[{', '.join(tp)}]" if tp else ""
            lines = [f"{pad}@{d}" for d in decos]
            first = f"{pad}class {sym.name}{tp_str}{base_str}:"
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
                    lines.extend(_emit_decl(m, name_map, indent=indent + 1))
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

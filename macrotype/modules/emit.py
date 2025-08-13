from __future__ import annotations

from typing import Any, ForwardRef, get_args, get_origin

INDENT = "    "

from .scanner import ModuleInfo
from .symbols import AliasSymbol, ClassSymbol, FuncSymbol, Symbol, VarSymbol


def emit_module(mi: ModuleInfo) -> list[str]:
    """Emit `.pyi` lines for a ModuleInfo using raw annotations only."""
    raw_annos = collect_all_annotations(mi)
    atoms = set()
    for ann in raw_annos:
        atoms |= flatten_annotation_atoms(ann)

    context = mi.mod.__dict__
    name_map = build_name_map(atoms, context)

    lines: list[str] = []
    for sym in mi.symbols:
        lines.extend(_emit_symbol(sym, name_map, indent=0))
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()

    # Collect typing imports
    typing_names = {name_map[a] for a in atoms if getattr(a, "__module__", None) == "typing"}

    pre: list[str] = []
    if typing_names:
        pre.append(f"from typing import {', '.join(sorted(typing_names))}")
        if lines:
            pre.append("")

    return pre + lines


def collect_all_annotations(mi: ModuleInfo) -> list[Any]:
    """Walk ModuleInfo and collect all raw annotations."""
    annos: list[Any] = []

    def visit(sym: Symbol):
        match sym:
            case VarSymbol(site=site):
                annos.append(site.raw)
            case AliasSymbol(value=site):
                annos.append(site.raw)
            case FuncSymbol(params=params, ret=ret):
                for p in params:
                    annos.append(p.raw)
                if ret:
                    annos.append(ret.raw)
            case ClassSymbol(bases=bases, td_fields=fields, members=members):
                for b in bases:
                    annos.append(b.raw)
                for f in fields:
                    annos.append(f.raw)
                for m in members:
                    visit(m)

    for s in mi.symbols:
        visit(s)
    return annos


def flatten_annotation_atoms(ann: Any) -> set[Any]:
    """Flatten all atomic components of a type annotation."""
    visited = set()
    atoms = set()
    stack = [ann]

    while stack:
        obj = stack.pop()
        if obj in visited:
            continue
        visited.add(obj)

        if isinstance(obj, ForwardRef):
            atoms.add(obj)
            continue

        origin = get_origin(obj)
        args = get_args(obj)

        if origin:
            atoms.add(origin)
            stack.extend(args)
        elif isinstance(args, tuple):
            atoms.add(obj)
            stack.extend(args)
        else:
            atoms.add(obj)

    return atoms


def build_name_map(atoms: set[Any], context: dict[str, Any]) -> dict[Any, str]:
    """Map annotation atoms to names based on module context."""
    reverse = {v: k for k, v in context.items()}
    name_map: dict[Any, str] = {}

    for atom in atoms:
        if isinstance(atom, ForwardRef):
            name_map[atom] = atom.__forward_arg__
        elif atom in reverse:
            name_map[atom] = reverse[atom]
        elif hasattr(atom, "__name__"):
            name_map[atom] = atom.__name__
        else:
            name_map[atom] = repr(atom)

    return name_map


def stringify_annotation(ann: Any, name_map: dict[Any, str]) -> str:
    """Emit string form of a type annotation."""
    if isinstance(ann, ForwardRef):
        return ann.__forward_arg__

    if isinstance(ann, str):
        return ann  # literal forward ref

    origin = get_origin(ann)
    args = get_args(ann)

    if origin:
        name = name_map.get(origin, getattr(origin, "__name__", repr(origin)))
        inner = ", ".join(stringify_annotation(arg, name_map) for arg in args)
        return f"{name}[{inner}]"
    else:
        return name_map.get(ann, repr(ann))


def _emit_symbol(sym: Symbol, name_map: dict[Any, str], *, indent: int) -> list[str]:
    pad = INDENT * indent

    match sym:
        case VarSymbol(site=site):
            ty = stringify_annotation(site.raw, name_map)
            return [f"{pad}{sym.name}: {ty}"]

        case AliasSymbol(value=site):
            ty = stringify_annotation(site.raw, name_map)
            return [f"{pad}type {sym.name} = {ty}"]

        case FuncSymbol(params=params, ret=ret, decorators=decos):
            pieces: list[str] = []
            for d in decos:
                pieces.append(f"{pad}@{d}")
            param_strs = [f"{p.name}: {stringify_annotation(p.raw, name_map)}" for p in params]
            ret_str = f" -> {stringify_annotation(ret.raw, name_map)}" if ret else ""
            pieces.append(f"{pad}def {sym.name}({', '.join(param_strs)}){ret_str}: ...")
            return pieces

        case ClassSymbol(bases=bases, td_fields=fields, members=members):
            base_str = ""
            if bases:
                base_str = f"({', '.join(stringify_annotation(b.raw, name_map) for b in bases)})"
            lines = [f"{pad}class {sym.name}{base_str}:"]
            if fields:
                for f in fields:
                    ty = stringify_annotation(f.raw, name_map)
                    lines.append(f"{pad}{INDENT}{f.name}: {ty}")
            if members:
                for m in members:
                    lines.extend(_emit_symbol(m, name_map, indent=indent + 1))
            if not fields and not members:
                lines.append(f"{pad}{INDENT}...")
            return lines

        case _:
            raise NotImplementedError(f"Unsupported symbol: {type(sym).__name__}")

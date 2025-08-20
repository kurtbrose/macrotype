from __future__ import annotations

import enum
import inspect
import types
from typing import Annotated, Any, Callable, ForwardRef, Iterable, get_args, get_origin

INDENT = "    "

import typing as t

_TYPING_ATTR_TYPES: tuple[type, ...] = (type, types.GenericAlias, str)
if hasattr(types, "UnionType"):
    _TYPING_ATTR_TYPES += (types.UnionType,)
TypeAliasType = getattr(t, "TypeAliasType", None)
if TypeAliasType is not None:
    _TYPING_ATTR_TYPES += (TypeAliasType,)

_UNION_ORIGINS: tuple[Any, ...] = (t.Union,)
if hasattr(types, "UnionType"):
    _UNION_ORIGINS += (types.UnionType,)


from .ir import AnnExpr, ClassDecl, Decl, FuncDecl, ModuleDecl, TypeDefDecl, VarDecl


def _qualname(obj: Any, default: str | None = None) -> str:
    """Return the best available name for *obj* honoring ``__qualname_override__``."""
    if default is None:
        default = repr(obj)
    name = getattr(obj, "__name__", default)
    if "<locals>." in name:
        name = name.split("<locals>.")[-1]
    return getattr(obj, "__qualname_override__", name)


def emit_module(mi: ModuleDecl) -> list[str]:
    """Emit `.pyi` lines for a ModuleDecl using annotations only."""
    annotations = collect_all_annotations(mi)
    atoms: dict[int, Any] = {}
    for ann in annotations:
        atoms.update(flatten_annotation_atoms(ann))
    for sym in mi.get_all_decls():
        if isinstance(sym, TypeDefDecl) and sym.value is not None:
            atoms.update(flatten_annotation_atoms(sym.value.annotation))

    context = mi.obj.__dict__
    name_map = build_name_map(atoms.values(), context)

    lines: list[str] = []
    for sym in mi.members:
        if not sym.emit:
            continue
        lines.extend(_emit_decl(sym, name_map, mi.obj.__name__, indent=0))
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()

    pre: list[str] = []
    if mi.source and mi.source.headers:
        pre.extend(mi.source.headers)
    imports = mi.imports.lines() if mi.imports else []
    pre.extend(imports)
    if lines:
        if pre:
            pre.append("")
        pre.extend(lines)
    return pre


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
            if site.annotation is not inspect._empty:
                annos.append(site.annotation)
    return annos


def _origin_and_args(obj: Any) -> tuple[Any | None, tuple[Any, ...]]:
    """Best-effort ``origin``/``args`` helper for arbitrary generics."""

    origin = get_origin(obj)
    if origin is not None:
        return origin, get_args(obj)
    if not isinstance(obj, type):
        try:
            type_attr = object.__getattribute__(obj, "type")
        except AttributeError:
            pass
        else:
            if isinstance(type_attr, _TYPING_ATTR_TYPES) or get_origin(type_attr) is not None:
                return type(obj), (type_attr,)
    return None, ()


def flatten_annotation_atoms(ann: Any) -> dict[int, Any]:
    """Flatten all atomic components of a type annotation."""
    visited: dict[int, Any] = {}
    atoms: dict[int, Any] = {}
    stack = [ann]

    while stack:
        obj = stack.pop()
        if isinstance(obj, AnnExpr):
            stack.append(obj.evaluated)
            continue
        obj_id = id(obj)
        if obj_id in visited:
            continue
        visited[obj_id] = obj

        origin, args = _origin_and_args(obj)

        if isinstance(obj, (list, tuple)) and origin is None:
            stack.extend(obj)
            continue

        if isinstance(obj, ForwardRef):
            atoms[obj_id] = obj
            continue

        if origin is Annotated:
            first, *metas = args
            stack.append(first)
            for meta in metas:
                atoms[id(meta)] = meta
            atoms[id(origin)] = origin
            continue

        if origin is not None:
            if origin in _UNION_ORIGINS:
                stack.extend(args)
                continue
            atoms[obj_id] = obj
            atoms[id(origin)] = origin
            stack.extend(args)
        elif args:
            atoms[obj_id] = obj
            stack.extend(args)
        else:
            atoms[obj_id] = obj

    return atoms


def build_name_map(atoms: Iterable[Any], context: dict[str, Any]) -> dict[int, str]:
    """Map annotation atoms to names based on module context."""
    module_name = context.get("__name__")
    reverse: dict[int, str] = {}
    primitives = (type(None), bool, int, float, complex, str, bytes)

    def _collect_nested(obj: Any, prefix: str) -> None:
        if not (inspect.isclass(obj) and getattr(obj, "__module__", None) == module_name):
            return
        obj_qual = getattr(obj, "__qualname__", "")
        for name, val in getattr(obj, "__dict__", {}).items():
            val_qual = getattr(val, "__qualname__", "")
            if inspect.isclass(val) and val_qual.startswith(obj_qual + "."):
                qual = f"{prefix}.{name}"
                reverse.setdefault(id(val), qual)
                _collect_nested(val, qual)

    for k, v in context.items():
        if isinstance(v, primitives) or inspect.isroutine(v):
            continue
        reverse.setdefault(id(v), k)
        _collect_nested(v, k)

    name_map: dict[int, str] = {}

    def _best_name(obj: Any) -> str:
        if isinstance(obj, primitives):
            return _qualname(obj)
        qual = getattr(obj, "__qualname__", None)
        if qual and "." in qual:
            return qual
        name = getattr(obj, "__name__", None)
        if name is not None:
            return name
        tname = getattr(type(obj), "__qualname__", getattr(type(obj), "__name__", None))
        if tname is not None:
            return tname
        return _qualname(obj)

    for atom in atoms:
        atom_id = id(atom)
        if isinstance(atom, ForwardRef):
            name_map[atom_id] = atom.__forward_arg__
            continue
        if atom_id in reverse:
            name = reverse[atom_id]
            mod = getattr(atom, "__module__", None)
            qual = _best_name(atom)
            if mod not in {module_name, "builtins"} and qual != name:
                name_map[atom_id] = qual
            else:
                name_map[atom_id] = name
            continue
        name_map[atom_id] = _best_name(atom)

    return name_map


def stringify_annotation(ann: Any, name_map: dict[int, str], module_name: str | None = None) -> str:
    """Emit string form of a type annotation."""
    if ann is Ellipsis:
        return "..."

    if isinstance(ann, AnnExpr):
        return ann.expr

    if isinstance(ann, ForwardRef):
        return ann.__forward_arg__

    if isinstance(ann, str):
        return repr(ann)

    if ann is type(None):
        return "None"

    if ann.__class__ is t.ParamSpecArgs:
        origin = getattr(ann, "__origin__", None)
        name = name_map.get(id(origin), _qualname(origin))
        return f"{name}.args"

    if ann.__class__ is t.ParamSpecKwargs:
        origin = getattr(ann, "__origin__", None)
        name = name_map.get(id(origin), _qualname(origin))
        return f"{name}.kwargs"

    origin, args = _origin_and_args(ann)

    if origin in {types.UnionType, t.Union}:
        items = [(arg, stringify_annotation(arg, name_map, module_name)) for arg in args]
        items.sort(key=lambda item: (0 if isinstance(item[0], t.TypeVar) else 1, item[1]))
        return " | ".join(s for _, s in items)

    from collections.abc import Callable as ABC_Callable

    if origin in {Callable, ABC_Callable}:
        if not args:
            return "Callable"
        name = name_map.get(id(origin), _qualname(origin, "Callable"))
        if len(args) == 2:
            params, ret = args
            ret_str = stringify_annotation(ret, name_map, module_name)
            if params is Ellipsis:
                return f"{name}[..., {ret_str}]"
            if isinstance(params, t.ParamSpec) or get_origin(params) is t.Concatenate:
                params_str = stringify_annotation(params, name_map, module_name)
                return f"{name}[{params_str}, {ret_str}]"
            if not isinstance(params, (list, tuple)):
                params = [params]
        else:
            *params, ret = args
            ret_str = stringify_annotation(ret, name_map, module_name)
        params_str = ", ".join(stringify_annotation(p, name_map, module_name) for p in params)
        return f"{name}[[{params_str}], {ret_str}]"

    if origin is t.Unpack:
        (inner,) = args
        if inner.__class__ is t.ParamSpecArgs:
            ps = getattr(inner, "__origin__", None)
            name = name_map.get(id(ps), _qualname(ps))
            return f"*{name}.args"
        if inner.__class__ is t.ParamSpecKwargs:
            ps = getattr(inner, "__origin__", None)
            name = name_map.get(id(ps), _qualname(ps))
            return f"**{name}.kwargs"
        return f"Unpack[{stringify_annotation(inner, name_map, module_name)}]"

    if origin is Annotated:
        first, *metas = args
        parts = [stringify_annotation(first, name_map, module_name)]
        for meta in metas:
            name = name_map.get(id(meta))
            if (
                name is not None
                and getattr(meta, "__module__", None) != module_name
                and "<locals>" not in name
            ):
                parts.append(name)
            else:
                parts.append(_qualname(meta))
        return f"Annotated[{', '.join(parts)}]"

    if origin is tuple and ann is not tuple and not args:
        name = name_map.get(id(origin), _qualname(origin))
        return f"{name}[()]"

    if origin is not None:
        name = name_map.get(id(origin), _qualname(origin))
        inner = ", ".join(stringify_annotation(arg, name_map, module_name) for arg in args)
        return f"{name}[{inner}]"
    else:
        return name_map.get(id(ann), _qualname(ann))


def stringify_value(val: Any, name_map: dict[int, str]) -> str:
    """Emit string form of a value used in an assignment."""
    if isinstance(val, enum.Enum):
        cls = val.__class__
        cls_name = name_map.get(id(cls), _qualname(cls))
        return f"{cls_name}.{val.name}"
    if isinstance(val, (int, float, bool)) or val is None:
        return repr(val)
    if isinstance(val, str):
        return repr(val)
    return name_map.get(id(val), repr(val))


def _emit_decl(sym: Decl, name_map: dict[int, str], module_name: str, *, indent: int) -> list[str]:
    if not sym.emit:
        return []
    pad = INDENT * indent

    match sym:
        case VarDecl(site=site):
            ty = stringify_annotation(site.annotation, name_map, module_name)
            line = f"{pad}{sym.name}: {ty}"
            line = _add_comment(line, sym.comment or site.comment)
            return [line]

        case TypeDefDecl(value=site, type_params=params, obj_type=alias):
            keyword = param_str = ""
            match alias:
                case None:
                    rhs = stringify_value(site.annotation, name_map)
                case t.TypeAliasType():  # type: ignore[attr-defined]
                    keyword = "type "
                    rhs = stringify_annotation(site.annotation, name_map, module_name)
                    param_str = f"[{', '.join(params)}]" if params else ""
                case t.TypeVar():
                    rhs = _stringify_typevar(alias, name_map, module_name)
                case t.ParamSpec():
                    rhs = _stringify_paramspec(alias)
                case t.TypeVarTuple():
                    rhs = _stringify_typevartuple(alias)
                case t.TypeAlias:  # type: ignore[misc]
                    rhs = stringify_annotation(site.annotation, name_map, module_name)
                case t.NewType:
                    ty = stringify_annotation(site.annotation, name_map, module_name)
                    rhs = f'NewType("{sym.name}", {ty})'
                case types.GenericAlias():
                    rhs = stringify_annotation(site.annotation, name_map, module_name)
                case _:
                    raise NotImplementedError(f"Unsupported alias type: {alias!r}")
            line = f"{pad}{keyword}{sym.name}{param_str} = {rhs}"
            line = _add_comment(line, sym.comment or site.comment)
            return [line]

        case FuncDecl(params=params, ret=ret, decorators=decos, type_params=tp, is_async=is_async):
            pieces: list[str] = []
            for d in decos:
                pieces.append(f"{pad}@{d}")
            param_strs: list[str] = []
            for p in params:
                name = p.name or ""
                if name in {"*", "/"}:
                    param_strs.append(name)
                    continue
                if p.annotation is inspect._empty:
                    param_strs.append(name)
                else:
                    param_strs.append(
                        f"{name}: {stringify_annotation(p.annotation, name_map, module_name)}"
                    )
            ret_str = (
                f" -> {stringify_annotation(ret.annotation, name_map, module_name)}" if ret else ""
            )
            tp_str = f"[{', '.join(tp)}]" if tp else ""
            prefix = "async " if is_async else ""
            line = f"{pad}{prefix}def {sym.name}{tp_str}({', '.join(param_strs)}){ret_str}: ..."
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
                base_str = f"({', '.join(stringify_annotation(b.annotation, name_map, module_name) for b in bases)})"
            tp_str = f"[{', '.join(tp)}]" if tp else ""
            lines = [f"{pad}@{d}" for d in decos]
            first = f"{pad}class {sym.name}{tp_str}{base_str}:"
            first = _add_comment(first, sym.comment)
            lines.append(first)
            if fields:
                for f in fields:
                    ty = stringify_annotation(f.annotation, name_map, module_name)
                    line = f"{pad}{INDENT}{f.name}: {ty}"
                    line = _add_comment(line, f.comment)
                    lines.append(line)
            if members:
                for m in members:
                    lines.extend(_emit_decl(m, name_map, module_name, indent=indent + 1))
            if not fields and not members:
                lines.append(f"{pad}{INDENT}...")
            return lines

        case _:
            raise NotImplementedError(f"Unsupported symbol: {type(sym).__name__}")


def _stringify_typevar(tv: t.TypeVar, name_map: dict[int, str], module_name: str) -> str:
    args = [f'"{tv.__name__}"']
    bound = getattr(tv, "__bound__", None)
    constraints = getattr(tv, "__constraints__", ())
    if bound is not None:
        args.append(f"bound={stringify_annotation(bound, name_map, module_name)}")
    elif constraints:
        args.extend(stringify_annotation(c, name_map, module_name) for c in constraints)
    if getattr(tv, "__covariant__", False):
        args.append("covariant=True")
    if getattr(tv, "__contravariant__", False):
        args.append("contravariant=True")
    if getattr(tv, "__infer_variance__", False):
        args.append("infer_variance=True")
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

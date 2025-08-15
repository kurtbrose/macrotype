from __future__ import annotations

import typing as t
from collections import defaultdict
from collections.abc import Callable as ABC_Callable
from typing import Callable, Iterable

from ..emit import (
    build_name_map,
    collect_all_annotations,
    flatten_annotation_atoms,
)
from ..ir import ClassDecl, Decl, ImportBlock, ModuleDecl, TypeDefDecl

_MODULE_ALIASES: dict[str, str] = {
    "pathlib._local": "pathlib",
    "pathlib._pathlib": "pathlib",
}


def resolve_imports(mi: ModuleDecl) -> None:
    annotations = collect_all_annotations(mi)
    atoms: dict[int, t.Any] = {}
    for ann in annotations:
        atoms.update(flatten_annotation_atoms(ann))

    context = mi.obj.__dict__
    name_map = build_name_map(atoms.values(), context)

    typing_names = {
        name_map[id(a)]
        for a in atoms.values()
        if getattr(a, "__module__", None) == "typing" or a is Callable or a is ABC_Callable
    }
    typing_names.update(_collect_typing_names(mi.members))

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

    mi.imports = ImportBlock(typing=typing_names, froms=dict(external))


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

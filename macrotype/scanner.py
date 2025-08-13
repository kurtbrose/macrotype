from __future__ import annotations

import inspect
import typing as t
from dataclasses import dataclass, replace
from types import ModuleType

from .types.symbols import (
    AliasSymbol,
    ClassSymbol,
    FuncSymbol,
    Provenance,
    Site,
    Symbol,
    VarSymbol,
)


@dataclass
class ModuleInfo:
    """Scanned representation of a Python module."""

    mod: ModuleType  # Original loaded module
    symbols: list[Symbol]
    provenance: str  # module name or synthetic name


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _source_prov(obj: t.Any, *, modname: str, key: str, name: str) -> Provenance:
    try:
        file = inspect.getsourcefile(obj)  # type: ignore[arg-type]
        lines, start = inspect.getsourcelines(obj)  # type: ignore[arg-type]
        line = start
    except Exception:
        file = None
        line = None
    qual = getattr(obj, "__qualname__", name)
    return Provenance(module=modname, qualname=qual, file=file, line=line)


def _mk_key(parent_key: str | None, modname: str, name: str) -> str:
    if parent_key:
        return f"{parent_key}.{name}"
    return f"{modname}.{name}"


def _get_modname(glb_or_mod: ModuleType | t.Mapping[str, t.Any]) -> str:
    if isinstance(glb_or_mod, ModuleType):
        return glb_or_mod.__name__
    return glb_or_mod.get("__name__", "<module>")  # type: ignore[union-attr]


def _get_globals(glb_or_mod: ModuleType | t.Mapping[str, t.Any]) -> dict[str, t.Any]:
    return vars(glb_or_mod) if isinstance(glb_or_mod, ModuleType) else dict(glb_or_mod)


def scan_module(glb_or_mod: ModuleType | t.Mapping[str, t.Any]) -> ModuleInfo:
    modname = _get_modname(glb_or_mod)
    glb = _get_globals(glb_or_mod)
    if isinstance(glb_or_mod, ModuleType):
        mod = glb_or_mod
    else:
        mod = ModuleType(modname)
        mod.__dict__.update(glb)
    mod_file = getattr(mod, "__file__", None)

    syms: list[Symbol] = []

    mod_ann: dict[str, t.Any] = glb.get("__annotations__", {}) or {}
    seen: set[str] = set()

    for name, obj in list(glb.items()):
        if _is_dunder(name):
            continue
        seen.add(name)

        if isinstance(obj, t.TypeAliasType):  # type: ignore[attr-defined]
            key = _mk_key(None, modname, name)
            prov = _source_prov(obj, modname=modname, key=key, name=name)
            site = Site(role="alias_value", raw=obj.__value__, prov=prov)
            syms.append(AliasSymbol(name=name, key=key, prov=prov, value=site))
            continue

        if inspect.isclass(obj):
            syms.append(_scan_class(obj, modname=modname, parent_key=None))
            continue

        if inspect.isfunction(obj):
            syms.append(_scan_function(obj, modname=modname, parent_key=None))
            continue

        if name in mod_ann:
            key = _mk_key(None, modname, name)
            ann = mod_ann[name]
            if ann is t.TypeAlias:
                prov = _source_prov(obj, modname=modname, key=key, name=name)
                site = Site(role="alias_value", raw=obj, prov=prov)
                syms.append(AliasSymbol(name=name, key=key, prov=prov, value=site))
            else:
                prov = _source_prov(obj, modname=modname, key=key, name=name)
                site = Site(role="var", name=name, raw=ann, prov=prov)
                syms.append(VarSymbol(name=name, key=key, prov=prov, site=site, initializer=obj))
            continue

        if hasattr(obj, "__name__") and getattr(obj, "__module__", None) != modname:
            key = _mk_key(None, modname, name)
            prov = _source_prov(obj, modname=modname, key=key, name=name)
            site = Site(role="alias_value", raw=obj, prov=prov)
            syms.append(AliasSymbol(name=name, key=key, prov=prov, value=site))
            continue

    for name, rann in mod_ann.items():
        if name in seen:
            continue
        key = _mk_key(None, modname, name)
        prov = Provenance(module=modname, qualname=name, file=mod_file, line=None)
        site = Site(role="var", name=name, raw=rann, prov=prov)
        syms.append(VarSymbol(name=name, key=key, prov=prov, site=site))

    return ModuleInfo(mod=mod, symbols=syms, provenance=modname)


def _scan_function(fn: t.Callable, *, modname: str, parent_key: str | None) -> FuncSymbol:
    name = getattr(fn, "__qualname_override__", fn.__name__)
    key = _mk_key(parent_key, modname, name.split(".")[-1])
    prov = _source_prov(fn, modname=modname, key=key, name=name)

    raw_ann: dict[str, t.Any] = getattr(fn, "__annotations__", {}) or {}
    params: list[Site] = []
    try:
        sig = inspect.signature(fn)
        for p in sig.parameters.values():
            if p.name in raw_ann:
                params.append(Site(role="param", name=p.name, raw=raw_ann[p.name], prov=prov))
    except (TypeError, ValueError):
        pass

    ret = None
    if "return" in raw_ann:
        ret = Site(role="return", raw=raw_ann["return"], prov=prov)

    decos: list[str] = []
    if getattr(fn, "__isabstractmethod__", False):
        decos.append("abstractmethod")

    return FuncSymbol(
        name=name.split(".")[-1],
        key=key,
        prov=prov,
        params=tuple(params),
        ret=ret,
        decorators=tuple(decos),
        overload_index=None,
    )


def _scan_class(cls: type, *, modname: str, parent_key: str | None) -> ClassSymbol:
    name = getattr(cls, "__qualname_override__", cls.__name__)
    key = _mk_key(parent_key, modname, name.split(".")[-1])
    prov = _source_prov(cls, modname=modname, key=key, name=name)

    bases_src = getattr(cls, "__orig_bases__", None) or cls.__bases__
    bases: list[Site] = []
    for i, b in enumerate(bases_src):
        if b is object:
            continue
        bases.append(Site(role="base", index=i, raw=b, prov=prov))

    is_td = isinstance(cls, getattr(t, "_TypedDictMeta", ()))
    td_total: bool | None = None
    td_fields: list[Site] = []
    if is_td:
        td_total = cls.__dict__.get("__total__", True)
        raw_ann = cls.__dict__.get("__annotations__", {}) or {}
        for fname, rann in raw_ann.items():
            td_fields.append(Site(role="td_field", name=fname, raw=rann, prov=prov))

    members: list[Symbol] = []

    class_ann: dict[str, t.Any] = cls.__dict__.get("__annotations__", {}) or {}
    for fname, rann in class_ann.items():
        if is_td:
            continue
        key_m = f"{key}.{fname}"
        prov_m = Provenance(module=modname, qualname=f"{name}.{fname}", file=prov.file, line=None)
        site = Site(role="var", name=fname, raw=rann, prov=prov_m)
        init_val = cls.__dict__.get(fname, Ellipsis)
        members.append(
            VarSymbol(name=fname, key=key_m, prov=prov_m, site=site, initializer=init_val)
        )

    for mname, attr in cls.__dict__.items():
        if _is_dunder(mname):
            continue
        raw = attr
        while hasattr(raw, "__wrapped__"):
            raw = raw.__wrapped__
        if inspect.isfunction(raw):
            members.append(_scan_function(raw, modname=modname, parent_key=key))
        elif isinstance(raw, staticmethod):
            fn = raw.__func__
            mem = _scan_function(fn, modname=modname, parent_key=key)
            mem = replace(mem, decorators=mem.decorators + ("staticmethod",))
            members.append(mem)
        elif isinstance(raw, classmethod):
            fn = raw.__func__
            mem = _scan_function(fn, modname=modname, parent_key=key)
            mem = replace(mem, decorators=mem.decorators + ("classmethod",))
            members.append(mem)
        elif isinstance(raw, property):
            if raw.fget is not None:
                mem = _scan_function(raw.fget, modname=modname, parent_key=key)
                mem = replace(mem, decorators=mem.decorators + ("property",))
                members.append(mem)
        elif inspect.isclass(raw) and raw.__qualname__.startswith(cls.__qualname__ + "."):
            members.append(_scan_class(raw, modname=modname, parent_key=key))

    return ClassSymbol(
        name=name.split(".")[-1],
        key=key,
        prov=prov,
        bases=tuple(bases),
        td_fields=tuple(td_fields),
        is_typeddict=is_td,
        td_total=td_total,
        members=tuple(members),
    )

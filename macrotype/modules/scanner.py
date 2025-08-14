from __future__ import annotations

import inspect
import typing as t
from dataclasses import replace
from types import ModuleType

from .ir import ClassDecl, Decl, FuncDecl, ModuleDecl, Site, TypeDefDecl, VarDecl


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def scan_module(mod: ModuleType) -> ModuleDecl:
    modname = mod.__name__
    glb = vars(mod)

    decls: list[Decl] = []

    mod_ann: dict[str, t.Any] = glb.get("__annotations__", {}) or {}
    seen: set[str] = set()

    for name, obj in list(glb.items()):
        if _is_dunder(name):
            continue
        seen.add(name)

        if isinstance(obj, t.TypeAliasType):  # type: ignore[attr-defined]
            site = Site(role="alias_value", annotation=obj.__value__)
            decls.append(TypeDefDecl(name=name, value=site, obj=obj))
            continue

        if inspect.isclass(obj):
            decls.append(_scan_class(obj))
            continue

        if inspect.isfunction(obj):
            decls.append(_scan_function(obj))
            continue

        if name in mod_ann:
            ann = mod_ann[name]
            if ann is t.TypeAlias:
                site = Site(role="alias_value", annotation=obj)
                decls.append(TypeDefDecl(name=name, value=site, obj=obj))
            else:
                site = Site(role="var", name=name, annotation=ann)
                decls.append(VarDecl(name=name, site=site, obj=obj))
            continue

        site = Site(role="var", name=name, annotation=type(obj))
        decls.append(VarDecl(name=name, site=site, obj=obj))

    for name, rann in mod_ann.items():
        if name in seen:
            continue
        site = Site(role="var", name=name, annotation=rann)
        decls.append(VarDecl(name=name, site=site))

    return ModuleDecl(name=modname, obj=mod, members=decls)


def _scan_function(fn: t.Callable) -> FuncDecl:
    name = getattr(fn, "__qualname_override__", fn.__name__)

    raw_ann: dict[str, t.Any] = getattr(fn, "__annotations__", {}) or {}
    params: list[Site] = []
    try:
        sig = inspect.signature(fn)
        for p in sig.parameters.values():
            if p.name in raw_ann:
                params.append(Site(role="param", name=p.name, annotation=raw_ann[p.name]))
    except (TypeError, ValueError):
        pass

    ret = None
    if "return" in raw_ann:
        ret = Site(role="return", annotation=raw_ann["return"])

    decos: list[str] = []
    if getattr(fn, "__isabstractmethod__", False):
        decos.append("abstractmethod")

    return FuncDecl(
        name=name.split(".")[-1],
        params=tuple(params),
        ret=ret,
        obj=fn,
        decorators=tuple(decos),
    )


def _scan_class(cls: type) -> ClassDecl:
    name = getattr(cls, "__qualname_override__", cls.__name__)

    bases_src = getattr(cls, "__orig_bases__", None) or cls.__bases__
    bases: list[Site] = []
    for i, b in enumerate(bases_src):
        if b is object:
            continue
        bases.append(Site(role="base", index=i, annotation=b))

    is_td = isinstance(cls, getattr(t, "_TypedDictMeta", ()))
    td_total: bool | None = None
    td_fields: list[Site] = []
    if is_td:
        td_total = cls.__dict__.get("__total__", True)
        raw_ann = cls.__dict__.get("__annotations__", {}) or {}
        for fname, rann in raw_ann.items():
            td_fields.append(Site(role="td_field", name=fname, annotation=rann))

    members: list[Decl] = []

    class_ann: dict[str, t.Any] = cls.__dict__.get("__annotations__", {}) or {}
    for fname, rann in class_ann.items():
        if is_td:
            continue
        site = Site(role="var", name=fname, annotation=rann)
        init_val = cls.__dict__.get(fname, Ellipsis)
        members.append(VarDecl(name=fname, site=site, obj=init_val))

    for mname, attr in cls.__dict__.items():
        raw = attr
        while hasattr(raw, "__wrapped__"):
            raw = raw.__wrapped__
        decorators: tuple[str, ...] = ()
        fn: t.Callable | None = None
        if inspect.isfunction(raw):
            fn = raw
        elif isinstance(raw, staticmethod):
            fn = raw.__func__
            decorators = ("staticmethod",)
        elif isinstance(raw, classmethod):
            fn = raw.__func__
            decorators = ("classmethod",)
        elif isinstance(raw, property):
            fn = raw.fget
            decorators = ("property",)
        elif inspect.isclass(raw) and raw.__qualname__.startswith(cls.__qualname__ + "."):
            members.append(_scan_class(raw))

        if fn:
            mem = _scan_function(fn)
            mem = replace(mem, decorators=mem.decorators + decorators)
            members.append(mem)

    return ClassDecl(
        name=name.split(".")[-1],
        bases=tuple(bases),
        td_fields=tuple(td_fields),
        is_typeddict=is_td,
        td_total=td_total,
        members=tuple(members),
        obj=cls,
        comment=None,
    )

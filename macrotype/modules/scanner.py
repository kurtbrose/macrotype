from __future__ import annotations

import inspect
import sys
import types
import typing as t
from dataclasses import replace
from types import ModuleType

from .ir import AnnExpr, ClassDecl, Decl, FuncDecl, ModuleDecl, Site, TypeDefDecl, VarDecl


def _eval_annotation(
    ann: t.Any, glb: dict[str, t.Any], lcl: dict[str, t.Any] | None = None
) -> t.Any:
    if isinstance(ann, str):
        expr = ann
        if (expr.startswith("'") and expr.endswith("'")) or (
            expr.startswith('"') and expr.endswith('"')
        ):
            expr = expr[1:-1]
        try:
            evaluated = eval(expr, glb, lcl or {})
        except Exception:  # pragma: no cover - fall back to original
            return ann
        origin = t.get_origin(evaluated)
        if "[" in expr and origin is None:
            # Some libraries (SQLAlchemy is the motivating case) implement
            # ``__class_getitem__`` to intentionally discard generic arguments
            # at runtime.  Evaluating ``Select[int]`` therefore yields the
            # plain ``Select`` class, erasing the user's type parameters and
            # defeating dynamic analysis.  Preserve the original expression so
            # we can re-emit those generics later.
            return AnnExpr(expr=expr, evaluated=evaluated)
        return evaluated
    return ann


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def scan_module(mod: ModuleType) -> ModuleDecl:
    modname = mod.__name__
    glb = vars(mod)

    decls: list[Decl] = []

    mod_ann: dict[str, t.Any] = glb.get("__annotations__", {}) or {}
    seen: set[str] = set()

    for name, obj in list(glb.items()):
        if _is_dunder(name) or name == "TYPE_CHECKING":
            continue
        seen.add(name)

        if isinstance(obj, t.TypeAliasType):  # type: ignore[attr-defined]
            site = Site(role="alias_value", annotation=obj.__value__)
            decls.append(TypeDefDecl(name=name, value=site, obj=obj))
            continue

        if inspect.isclass(obj):
            if getattr(obj, "__module__", None) != modname:
                continue
            qualname = getattr(obj, "__qualname_override__", obj.__name__)
            if qualname != name:
                site = Site(role="alias_value", annotation=obj)
                decls.append(TypeDefDecl(name=name, value=site, obj=obj))
            else:
                decls.append(_scan_class(obj))
            continue

        if inspect.isfunction(obj):
            if obj.__name__ == "<lambda>":
                ann = _eval_annotation(mod_ann.get(name, type(obj)), glb)
                site = Site(role="var", name=name, annotation=ann)
                decls.append(VarDecl(name=name, site=site, obj=obj))
            else:
                qualname = getattr(obj, "__qualname_override__", obj.__name__)
                if qualname != name:
                    site = Site(role="alias_value", annotation=obj)
                    decls.append(TypeDefDecl(name=name, value=site, obj=obj))
                else:
                    decls.append(_scan_function(obj))
            continue

        if name in mod_ann:
            ann = _eval_annotation(mod_ann[name], glb)
            if ann is t.TypeAlias:
                site = Site(role="alias_value", annotation=obj)
                decls.append(TypeDefDecl(name=name, value=site, obj=obj))
            else:
                site = Site(role="var", name=name, annotation=ann)
                decls.append(VarDecl(name=name, site=site, obj=obj))
            continue

        ann = type(obj)
        if obj is None or isinstance(obj, (bool, int, float, complex, str, bytes)):
            if obj is None:
                ann = t.Any
            site = Site(role="var", name=name, annotation=ann)
            decls.append(VarDecl(name=name, site=site, obj=obj))
            continue
        if (
            isinstance(obj, t.TypeVar)
            or obj.__class__ is t.ParamSpec
            or obj.__class__ is t.TypeVarTuple
        ):
            site = Site(role="alias_value", annotation=obj)
            decls.append(TypeDefDecl(name=name, value=site, obj=obj, obj_type=obj))
            continue
        if hasattr(obj, "__supertype__"):
            site = Site(role="alias_value", annotation=getattr(obj, "__supertype__"))
            decls.append(TypeDefDecl(name=name, value=site, obj=obj, obj_type=t.NewType))
            continue
        if isinstance(obj, types.GenericAlias):
            site = Site(role="alias_value", annotation=obj)
            decls.append(TypeDefDecl(name=name, value=site, obj=obj, obj_type=types.GenericAlias))
            continue
        if hasattr(obj, "__module__") and obj.__module__ != modname:
            obj_name = getattr(obj, "__name__", None)
            if obj_name == name:
                continue
            orig_mod = sys.modules.get(obj.__module__)
            if orig_mod is not None and getattr(orig_mod, name, None) is obj:
                continue
            if callable(obj) and obj_name is None:
                site = Site(role="var", name=name, annotation=ann)
                decls.append(VarDecl(name=name, site=site, obj=obj))
            else:
                site = Site(role="alias_value", annotation=obj)
                decls.append(TypeDefDecl(name=name, value=site, obj=obj))
            continue
        if callable(obj):
            site = Site(role="var", name=name, annotation=ann)
            decls.append(VarDecl(name=name, site=site, obj=obj))
            continue
        continue

    for name, rann in mod_ann.items():
        if name in seen or name == "TYPE_CHECKING":
            continue
        ann = _eval_annotation(rann, glb)
        site = Site(role="var", name=name, annotation=ann)
        decls.append(VarDecl(name=name, site=site))

    return ModuleDecl(name=modname, obj=mod, members=decls)


def _scan_function(fn: t.Callable) -> FuncDecl:
    name = getattr(fn, "__qualname_override__", fn.__name__)

    raw_ann: dict[str, t.Any] = getattr(fn, "__annotations__", {}) or {}
    params: list[Site] = []
    glb = getattr(fn, "__globals__", {})
    lcl = {tp.__name__: tp for tp in getattr(fn, "__type_params__", ())}
    try:
        sig = inspect.signature(fn)
        for p in sig.parameters.values():
            ann = raw_ann.get(p.name, inspect._empty)
            if ann is not inspect._empty:
                ann = _eval_annotation(ann, glb, lcl)
            params.append(Site(role="param", name=p.name, annotation=ann))
    except (TypeError, ValueError):
        params.append(Site(role="param", name="...", annotation=t.Any))

    ret = None
    if "return" in raw_ann:
        ann = _eval_annotation(raw_ann["return"], glb, lcl)
        ret = Site(role="return", annotation=ann)
    elif params and params[0].name == "...":
        ann: t.Any = fn if isinstance(fn, type) else t.Any
        ret = Site(role="return", annotation=ann)

    decos: list[str] = []
    if getattr(fn, "__isabstractmethod__", False):
        decos.append("abstractmethod")

    is_async = inspect.iscoroutinefunction(fn) or inspect.isasyncgenfunction(fn)

    return FuncDecl(
        name=name.split(".")[-1],
        params=tuple(params),
        ret=ret,
        obj=fn,
        decorators=tuple(decos),
        is_async=is_async,
    )


def _declared_bases_for_stub(cls: type) -> tuple[t.Any, ...]:
    declared: list[t.Any] = list(getattr(cls, "__orig_bases__", ()))
    if not declared:
        declared = list(cls.__bases__)
    mro_set = set(cls.__mro__)
    rt = tuple(cls.__bases__)

    out: list[t.Any] = []
    special: set[t.Any] = {t.TypedDict, t.NamedTuple}
    proto = getattr(t, "Protocol", None)
    if proto is not None:
        special.add(proto)

    for db in declared:
        if db in special:
            out.append(db)
            continue

        origin = t.get_origin(db) or db
        if origin in special:
            out.append(db)
            continue
        if not isinstance(origin, type):
            continue
        if isinstance(origin, getattr(t, "_TypedDictMeta", ())):
            out.append(db)
            continue
        if origin in rt:
            out.append(db)
            continue
        matched = False
        for rb in rt:
            rb_origin = t.get_origin(rb) or rb
            if rb_origin is origin:
                matched = True
                break
        if matched:
            out.append(db)
            continue

    if not out:
        filtered = [b for b in rt if not getattr(b, "__module__", "").startswith("sqlalchemy.")]
        out = filtered or list(rt)

    return tuple(out)


def _scan_class(cls: type) -> ClassDecl:
    name = getattr(cls, "__qualname_override__", cls.__name__)
    bases_src = _declared_bases_for_stub(cls)
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
        mod = sys.modules.get(cls.__module__)
        glb = mod.__dict__ if mod else {}
        for fname, rann in raw_ann.items():
            ann = _eval_annotation(rann, glb, dict(cls.__dict__))
            td_fields.append(Site(role="td_field", name=fname, annotation=ann))

    members: list[Decl] = []

    class_ann: dict[str, t.Any] = cls.__dict__.get("__annotations__", {}) or {}
    mod = sys.modules.get(cls.__module__)
    glb = mod.__dict__ if mod else {}
    for fname, rann in class_ann.items():
        if is_td:
            continue
        ann = _eval_annotation(rann, glb, dict(cls.__dict__))
        site = Site(role="var", name=fname, annotation=ann)
        init_val = cls.__dict__.get(fname, Ellipsis)
        members.append(VarDecl(name=fname, site=site, obj=init_val))

    for mname, attr in cls.__dict__.items():
        raw = attr
        while hasattr(raw, "__wrapped__"):
            raw = raw.__wrapped__
        decorators: tuple[str, ...] = ()
        fn: t.Callable | None = None
        if inspect.isfunction(raw) and getattr(raw, "__module__", None) == cls.__module__:
            fn = raw
        elif isinstance(raw, staticmethod):
            fn = raw.__func__
            if getattr(fn, "__module__", None) != cls.__module__:
                fn = None
            else:
                decorators = ("staticmethod",)
        elif isinstance(raw, classmethod):
            fn = raw.__func__
            if getattr(fn, "__module__", None) != cls.__module__:
                fn = None
            else:
                decorators = ("classmethod",)
        elif isinstance(raw, property):
            fn = raw.fget
            if fn and getattr(fn, "__module__", None) != cls.__module__:
                fn = None
            else:
                decorators = ("property",)
        elif (
            inspect.isclass(raw)
            and getattr(raw, "__module__", None) == cls.__module__
            and raw.__qualname__.startswith(cls.__qualname__ + ".")
        ):
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

from __future__ import annotations

"""Normalize method descriptors into function symbols."""

import functools
import inspect
from dataclasses import replace
from typing import Any

from macrotype.modules.ir import ClassDecl, FuncDecl, ModuleDecl
from macrotype.modules.scanner import _scan_function

# Mapping of descriptor types to the attribute holding the underlying
# function and the decorator string to attach.
_ATTR_DECORATORS: dict[type, tuple[str, str]] = {
    classmethod: ("__func__", "classmethod"),
    staticmethod: ("__func__", "staticmethod"),
    property: ("fget", "property"),
    functools.cached_property: ("func", "cached_property"),
}


def _unwrap_descriptor(obj: Any) -> Any | None:
    """Return the underlying descriptor for *obj* if wrapped."""

    while True:
        for typ in _ATTR_DECORATORS:
            if isinstance(obj, typ):
                return obj
        if hasattr(obj, "__wrapped__"):
            obj = obj.__wrapped__
            continue
        return None


def _extract_partialmethod(
    pm: functools.partialmethod, cls: type, name: str
) -> Any:  # pragma: no cover - thin wrapper around stdlib behaviour
    """Return a function object for ``partialmethod`` *pm* defined on *cls*."""

    fn = pm.__get__(None, cls)
    hints = getattr(pm.func, "__annotations__", {}).copy()
    sig_params = inspect.signature(fn).parameters
    fn.__annotations__ = {k: hints[k] for k in sig_params if k in hints}
    if "return" in hints:
        fn.__annotations__["return"] = hints["return"]
    fn.__name__ = name
    return fn


def _descriptor_members(attr_name: str, attr: Any, cls: type) -> list[FuncDecl]:
    """Return function symbols generated from descriptor *attr*."""

    unwrapped = _unwrap_descriptor(attr) or attr

    for attr_type, (func_attr, deco) in _ATTR_DECORATORS.items():
        if isinstance(unwrapped, attr_type):
            fn_obj = getattr(unwrapped, func_attr)
            for flag in ("__final__", "__override__", "__isabstractmethod__"):
                if getattr(attr, flag, False) and not getattr(fn_obj, flag, False):
                    setattr(fn_obj, flag, True)

            fn_sym = _scan_function(fn_obj)
            fn_sym = replace(fn_sym, name=attr_name, decorators=fn_sym.decorators + (deco,))
            members = [fn_sym]

            if attr_type is property:
                if unwrapped.fset is not None:
                    setter = _scan_function(unwrapped.fset)
                    setter = replace(
                        setter,
                        name=attr_name,
                        decorators=setter.decorators + (f"{attr_name}.setter",),
                    )
                    members.append(setter)
                if unwrapped.fdel is not None:
                    deleter = _scan_function(unwrapped.fdel)
                    deleter = replace(
                        deleter,
                        name=attr_name,
                        decorators=deleter.decorators + (f"{attr_name}.deleter",),
                    )
                    members.append(deleter)

            return members

    if isinstance(unwrapped, functools.partialmethod):
        fn_obj = _extract_partialmethod(unwrapped, cls, attr_name)
        for flag in ("__final__", "__override__", "__isabstractmethod__"):
            if getattr(attr, flag, False) and not getattr(fn_obj, flag, False):
                setattr(fn_obj, flag, True)
        fn_sym = _scan_function(fn_obj)
        fn_sym = replace(fn_sym, name=attr_name)
        return [fn_sym]

    return []


def _transform_class(sym: ClassDecl, cls: type) -> None:
    members = list(sym.members)

    for attr_name, attr in cls.__dict__.items():
        desc_members = _descriptor_members(attr_name, attr, cls)
        if desc_members:
            for i, m in enumerate(members):
                if m.name == attr_name:
                    members[i : i + 1] = desc_members
                    break
            else:
                members.extend(desc_members)

    sym.members = tuple(members)

    for m in sym.members:
        if isinstance(m, ClassDecl):
            inner = m.obj
            if isinstance(inner, type):
                _transform_class(m, inner)


def normalize_descriptors(mi: ModuleDecl) -> None:
    """Normalize descriptors within ``mi`` into function symbols."""

    for sym in mi.get_all_decls():
        if isinstance(sym, ClassDecl):
            cls = sym.obj
            if isinstance(cls, type):
                _transform_class(sym, cls)

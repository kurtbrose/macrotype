from __future__ import annotations

"""Normalize method descriptors into function symbols."""

import functools
from dataclasses import replace
from typing import Any

from .scanner import ModuleInfo, _scan_function
from .symbols import ClassSymbol, FuncSymbol

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


def _descriptor_members(attr_name: str, attr: Any) -> list[FuncSymbol]:
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

    return []


def _transform_class(sym: ClassSymbol, cls: type) -> None:
    members = list(sym.members)

    for attr_name, attr in cls.__dict__.items():
        desc_members = _descriptor_members(attr_name, attr)
        if desc_members:
            for i, m in enumerate(members):
                if m.name == attr_name:
                    members[i : i + 1] = desc_members
                    break
            else:
                members.extend(desc_members)

    sym.members = tuple(members)

    for m in sym.members:
        if isinstance(m, ClassSymbol):
            inner = getattr(cls, m.name, None)
            if isinstance(inner, type):
                _transform_class(m, inner)


def normalize_descriptors(mi: ModuleInfo) -> None:
    """Normalize descriptors within ``mi`` into function symbols."""

    for sym in mi.symbols:
        if isinstance(sym, ClassSymbol):
            cls = getattr(mi.mod, sym.name, None)
            if isinstance(cls, type):
                _transform_class(sym, cls)

from __future__ import annotations

from typing import Any

from macrotype.modules.ir import ClassDecl, ModuleDecl

# Default values used by @dataclass_transform.
_DT_DEFAULTS = {
    "eq_default": True,
    "order_default": False,
    "kw_only_default": False,
    "frozen_default": False,
}


def has_transform(cls: type) -> bool:
    """Return True if *cls* is covered by ``@dataclass_transform``."""

    if "__dataclass_transform__" in getattr(cls, "__dict__", {}):
        return True
    mcls = type(cls)
    if "__dataclass_transform__" in getattr(mcls, "__dict__", {}):
        return True
    for base in cls.__mro__[1:]:
        if "__dataclass_transform__" in getattr(base, "__dict__", {}):
            return True
    return False


def _dt_decorator(obj: Any) -> str | None:
    data = getattr(obj, "__dataclass_transform__", None)
    if not isinstance(data, dict):
        return None
    args: list[str] = []
    for name, default in _DT_DEFAULTS.items():
        val = data.get(name, default)
        if val != default:
            args.append(f"{name}={val}")
    return "dataclass_transform" + (f"({', '.join(args)})" if args else "()")


def apply_dataclass_transform(mi: ModuleDecl) -> None:
    """Attach ``@dataclass_transform`` decorators and strip unsafe ``__init__``."""

    for sym in mi.get_all_decls():
        if not isinstance(sym, ClassDecl):
            continue
        cls = sym.obj
        if not isinstance(cls, type):
            continue
        if "__dataclass_transform__" in getattr(cls, "__dict__", {}):
            deco = _dt_decorator(cls)
            if deco:
                sym.decorators = sym.decorators + (deco,)
            continue
        if has_transform(cls):
            sym.members = tuple(
                m for m in sym.members if not (m.name == "__init__" and hasattr(m, "params"))
            )
            sym.decorators = tuple(d for d in sym.decorators if not d.startswith("dataclass"))


__all__ = ["apply_dataclass_transform", "has_transform"]

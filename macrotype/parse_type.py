from __future__ import annotations

import collections.abc as abc
import enum
import types as _types
import typing as t
from dataclasses import dataclass
from typing import Optional, get_args, get_origin

from .types_ir import (
    LitVal,
    Ty,
    TyAnnotated,
    TyAny,
    TyApp,
    TyCallable,
    TyClassVar,
    TyForward,
    TyLiteral,
    TyName,
    TyNever,
    TyParamSpec,
    TyTuple,
    TyTypeVar,
    TyTypeVarTuple,
    TyUnion,
    TyUnpack,
)

# ---------- Environment (minimal) ----------


@dataclass(frozen=True)
class ParseEnv:
    """Scope info used during parsing. Extend as needed."""

    module: Optional[str] = None
    typevars: dict[str, TyTypeVar] = None  # name -> TyTypeVar
    in_typed_dict: bool = False  # lets callers capture Required/NotRequired

    def get_tv(self, name: str) -> Optional[TyTypeVar]:
        if not self.typevars:
            return None
        return self.typevars.get(name)


# ---------- Helpers ----------


def _tyname_of(obj: object) -> Ty:
    # ForwardRef-like strings (e.g., "User")
    if isinstance(obj, str):
        return TyForward(qualname=obj)

    # typing.ForwardRef instance (Py <=3.12 exposed), PEP 649 may differ
    if obj.__class__.__name__ == "ForwardRef":  # no direct import dep
        # repr(obj) often shows the string; try .arg first if present
        q = getattr(obj, "arg", None) or str(obj)
        return TyForward(qualname=q)

    # Any / Never / NoReturn / bare Final
    if obj is t.Any:
        return TyAny()
    if obj in (t.Never, t.NoReturn):
        return TyNever()
    if obj is t.Final:
        return TyAny()

    # None value / NoneType
    if obj is None or obj is type(None):  # noqa: E721
        return TyName(module="builtins", name="None")

    # Ellipsis literal
    if obj is Ellipsis:
        return TyName(module="builtins", name="Ellipsis")

    # TypeVar / ParamSpec / TypeVarTuple at use-site
    if isinstance(obj, t.TypeVar):
        return TyTypeVar(
            name=obj.__name__,
            bound=_maybe_to_ir(getattr(obj, "__bound__", None)),
            constraints=tuple(_maybe_to_ir(c) for c in getattr(obj, "__constraints__", ()) or ()),
            cov=getattr(obj, "__covariant__", False),
            contrav=getattr(obj, "__contravariant__", False),
        )

    if hasattr(obj, "__class__") and obj.__class__ is t.ParamSpec:
        return TyParamSpec(name=obj.__name__)  # type: ignore[attr-defined]

    if hasattr(obj, "__class__") and obj.__class__ is t.TypeVarTuple:
        return TyTypeVarTuple(name=obj.__name__)  # type: ignore[attr-defined]

    # Classes / aliases → TyName(module, qualname)
    mod = getattr(obj, "__module__", None)
    qn = getattr(obj, "__qualname__", None) or getattr(obj, "__name__", None)
    if mod and qn:
        return TyName(module=mod, name=qn)

    # Fallback (opaque)
    return TyName(module=None, name=repr(obj))


def _maybe_to_ir(tp: object | None, env: Optional[ParseEnv] = None) -> Ty | None:
    return None if tp is None else to_ir(tp, env or ParseEnv())


def _litval_of(val: object) -> LitVal:
    # Accept PEP 586 primitives / Enum / nested tuples; otherwise pass-through (repr-safe)
    if isinstance(val, (int, bool, str, bytes)) or val is None or isinstance(val, enum.Enum):
        return val  # type: ignore[return-value]
    if isinstance(val, tuple):
        return tuple(_litval_of(x) for x in val)  # type: ignore[return-value]
    # Non-strict: keep as-is (you can tighten later)
    return val  # type: ignore[return-value]


# ---------- Main parser ----------


def to_ir(tp: object, env: Optional[ParseEnv] = None) -> Ty:
    """Parse a Python typing object into IR. Non-strict; preserves opaque bits."""
    env = env or ParseEnv()

    # Fast path: leafy names / special singletons
    origin = get_origin(tp)
    if origin is None:
        return _tyname_of(tp)

    args = get_args(tp)

    # --- Union (X | Y) ---
    if origin in (t.Union, _types.UnionType):
        opts: list[Ty] = []
        for a in args:
            ir = to_ir(a, env)
            if isinstance(ir, TyUnion):
                opts.extend(ir.options)
            else:
                opts.append(ir)
        # Deduplicate and sort for order-insensitivity
        uniq: dict[str, Ty] = {repr(o): o for o in opts}
        return TyUnion(options=tuple(sorted(uniq.values(), key=repr)))

    # --- Annotated[T, ...] ---
    if origin is t.Annotated:
        base, *meta = args
        return TyAnnotated(base=to_ir(base, env), anno=tuple(meta))

    # --- Literal[...] ---
    if origin is t.Literal:
        return TyLiteral(values=tuple(_litval_of(a) for a in args))

    # --- ClassVar[T] ---
    if origin is t.ClassVar:
        (inner,) = args or (t.Any,)
        return TyClassVar(inner=to_ir(inner, env))

    # --- Final[T] / Final (unwrap; mark at symbol layer, not here) ---
    if origin is t.Final:
        inner = args[0] if args else t.Any
        return to_ir(inner, env)

    # --- Required/NotRequired (unwrap; TD field metadata handled by caller) ---
    if origin in (t.Required, t.NotRequired):
        (inner,) = args or (t.Any,)
        return to_ir(inner, env)

    # --- Tuple[...] ---
    if origin is tuple:
        # tuple[int, str] vs variadic tuple[T, ...]
        if args and args[-1] is Ellipsis:
            items = tuple(to_ir(a, env) for a in args[:-1]) + (
                TyName(module="builtins", name="Ellipsis"),
            )
            return TyApp(base=TyName(module="builtins", name="tuple"), args=items)
        return TyTuple(items=tuple(to_ir(a, env) for a in args))

    # --- Callable[...] ---
    if origin in (t.Callable, abc.Callable):
        if args and args[0] is Ellipsis:
            # Callable[..., R]
            return TyCallable(params=Ellipsis, ret=to_ir(args[1], env))
        if args and isinstance(args[0], (list, tuple)):
            params = tuple(to_ir(a, env) for a in args[0])
            ret = to_ir(args[1], env)
            return TyCallable(params=params, ret=ret)
        if args:
            return TyCallable(params=(to_ir(args[0], env),), ret=to_ir(args[1], env))
        return TyCallable(params=Ellipsis, ret=TyAny())

    # --- Unpack[...] (PEP 646) ---
    if origin is t.Unpack:
        (inner,) = args
        return TyUnpack(inner=to_ir(inner, env))

    # --- Concatenate[...] (treat as TyApp for now; you can special-case later) ---
    if getattr(t, "Concatenate", None) is origin:
        return TyApp(
            base=TyName(module="typing", name="Concatenate"),
            args=tuple(to_ir(a, env) for a in args),
        )

    # --- Type[...] (a/k/a builtins.type) ---
    if origin is type:
        return TyApp(
            base=TyName(module="builtins", name="type"), args=tuple(to_ir(a, env) for a in args)
        )

    # --- ParamSpec at use-site inside Callable etc. (already handled as leaf) ---

    # --- Default: generic application ---
    if getattr(tp, "__module__", None) == "typing":
        base = _tyname_of(tp)
    else:
        base = to_ir(origin, env)
    return TyApp(base=base, args=tuple(to_ir(a, env) for a in args))


# Notes:
#
#     Final, Required, NotRequired are unwrapped here (flags belong to the symbol/TypedDict field layer).
#
#     Unknown/future typing.Foo[...] falls back to TyApp(TyName("typing","Foo"), args_ir) — lossless, pass‑through.
#
#     Forward references handled both as strings and typing.ForwardRef.

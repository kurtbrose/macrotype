from __future__ import annotations

import collections.abc as abc
import enum
import types as _types
import typing as t
from dataclasses import dataclass, replace
from typing import Optional, get_args, get_origin

from .ir import (
    LitVal,
    ParsedTy,
    Ty,
    TyAnnoTree,
    TyAny,
    TyApp,
    TyCallable,
    TyForward,
    TyLiteral,
    TyName,
    TyNever,
    TyParamSpec,
    TyRoot,
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

    # typing.ForwardRef instance (attribute name differs across versions)
    if obj.__class__.__name__ == "ForwardRef":  # no direct import dep
        q = getattr(obj, "__forward_arg__", None) or getattr(obj, "arg", None) or str(obj)
        return TyForward(qualname=q)

    # Any / Never / NoReturn / bare Final
    if obj is t.Any:
        return TyAny()
    if obj in (t.Never, t.NoReturn):
        return TyNever()

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
    return None if tp is None else _to_ir(tp, env or ParseEnv())


def _litval_of(val: object) -> LitVal:
    # Accept PEP 586 primitives / Enum / nested tuples; otherwise pass-through (repr-safe)
    if isinstance(val, (int, bool, str, bytes)) or val is None or isinstance(val, enum.Enum):
        return val  # type: ignore[return-value]
    if isinstance(val, tuple):
        return tuple(_litval_of(x) for x in val)  # type: ignore[return-value]
    # Non-strict: keep as-is (you can tighten later)
    return val  # type: ignore[return-value]


# ---------- Main parser ----------


def _to_ir(tp: object, env: ParseEnv) -> TyRoot:
    """Parse a Python typing object into IR. Non-strict; preserves opaque bits."""

    origin = get_origin(tp)
    if origin is None:
        if tp is t.ClassVar:
            return TyRoot(ty=TyAny(), is_classvar=True)
        if tp is t.Final:
            return TyRoot(ty=TyAny(), is_final=True)
        if tp is t.Required:
            return TyRoot(ty=TyAny(), is_required=True)
        if tp is t.NotRequired:
            return TyRoot(ty=TyAny(), is_required=False)
        return TyRoot(ty=_tyname_of(tp))

    args = get_args(tp)

    if origin in (t.Union, _types.UnionType):
        opts: list[Ty] = []
        for a in args:
            ir = _to_ir(a, env)
            opts.append(ir.ty)
        uniq: dict[str, Ty] = {repr(o): o for o in opts}
        return TyRoot(ty=TyUnion(options=tuple(sorted(uniq.values(), key=repr))))

    if origin is t.Annotated:
        base, *meta = args
        inner = _to_ir(base, env)
        ann = TyAnnoTree(annos=tuple(meta), child=inner.ty.annotations)
        return TyRoot(
            ty=replace(inner.ty, annotations=ann),
            is_final=inner.is_final,
            is_required=inner.is_required,
            is_classvar=inner.is_classvar,
        )

    if origin is t.Literal:
        return TyRoot(ty=TyLiteral(values=tuple(_litval_of(a) for a in args)))

    if origin is t.ClassVar:
        (inner,) = args or (t.Any,)
        inner_tt = _to_ir(inner, env)
        return TyRoot(
            ty=inner_tt.ty,
            is_final=inner_tt.is_final,
            is_required=inner_tt.is_required,
            is_classvar=True,
        )

    if origin is t.Final:
        inner = args[0] if args else t.Any
        inner_tt = _to_ir(inner, env)
        return TyRoot(
            ty=inner_tt.ty,
            is_final=True,
            is_required=inner_tt.is_required,
            is_classvar=inner_tt.is_classvar,
        )

    if origin in (t.Required, t.NotRequired):
        (inner,) = args or (t.Any,)
        inner_tt = _to_ir(inner, env)
        req = True if origin is t.Required else False
        return TyRoot(
            ty=inner_tt.ty,
            is_final=inner_tt.is_final,
            is_required=req,
            is_classvar=inner_tt.is_classvar,
        )

    if origin is tuple:
        if args and args[-1] is Ellipsis:
            items = tuple(_to_ir(a, env).ty for a in args[:-1]) + (
                TyName(module="builtins", name="Ellipsis"),
            )
            return TyRoot(ty=TyApp(base=TyName(module="builtins", name="tuple"), args=items))
        return TyRoot(ty=TyTuple(items=tuple(_to_ir(a, env).ty for a in args)))

    if origin in (t.Callable, abc.Callable):
        if args and args[0] is Ellipsis:
            return TyRoot(ty=TyCallable(params=Ellipsis, ret=_to_ir(args[1], env).ty))
        if args and isinstance(args[0], (list, tuple)):
            params = tuple(_to_ir(a, env).ty for a in args[0])
            ret = _to_ir(args[1], env).ty
            return TyRoot(ty=TyCallable(params=params, ret=ret))
        if args:
            return TyRoot(
                ty=TyCallable(
                    params=(_to_ir(args[0], env).ty,),
                    ret=_to_ir(args[1], env).ty,
                )
            )
        return TyRoot(ty=TyCallable(params=Ellipsis, ret=TyAny()))

    if origin is t.Unpack:
        (inner,) = args
        return TyRoot(ty=TyUnpack(inner=_to_ir(inner, env).ty))

    if getattr(t, "Concatenate", None) is origin:
        return TyRoot(
            ty=TyApp(
                base=TyName(module="typing", name="Concatenate"),
                args=tuple(_to_ir(a, env).ty for a in args),
            )
        )

    if origin is type:
        return TyRoot(
            ty=TyApp(
                base=TyName(module="builtins", name="type"),
                args=tuple(_to_ir(a, env).ty for a in args),
            )
        )

    if getattr(tp, "__module__", None) == "typing":
        base = _tyname_of(tp)
    else:
        base = _to_ir(origin, env).ty
    return TyRoot(ty=TyApp(base=base, args=tuple(_to_ir(a, env).ty for a in args)))


def parse(tp: object, env: Optional[ParseEnv] = None) -> ParsedTy:
    return ParsedTy(_to_ir(tp, env or ParseEnv()))


# Notes:
#
#     Final, ClassVar, Required, NotRequired are modeled via flags on ``TyRoot``.
#
#     Unknown/future typing.Foo[...] falls back to ``TyApp(TyName("typing","Foo"), args_ir)`` — lossless, pass‑through.
#
#     Forward references handled both as strings and ``typing.ForwardRef``.

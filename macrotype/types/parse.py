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
    Qualifier,
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
    TyTop,
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


def _to_ir(tp: object, env: ParseEnv) -> TyTop:
    """Parse a Python typing object into IR. Non-strict; preserves opaque bits."""

    origin = get_origin(tp)
    if origin is None:
        if tp is t.ClassVar:
            return TyTop(ty=TyAny(), qualifiers=frozenset({Qualifier.CLASSVAR}))
        if tp is t.Final:
            return TyTop(ty=TyAny(), qualifiers=frozenset({Qualifier.FINAL}))
        if tp is t.Required:
            return TyTop(ty=TyAny(), qualifiers=frozenset({Qualifier.REQUIRED}))
        if tp is t.NotRequired:
            return TyTop(ty=TyAny(), qualifiers=frozenset({Qualifier.NOTREQUIRED}))
        return TyTop(ty=_tyname_of(tp), qualifiers=frozenset())

    args = get_args(tp)

    if origin in (t.Union, _types.UnionType):
        opts: list[Ty] = []
        for a in args:
            ir = _to_ir(a, env)
            opts.append(ir.ty)
        uniq: dict[str, Ty] = {repr(o): o for o in opts}
        return TyTop(
            ty=TyUnion(options=tuple(sorted(uniq.values(), key=repr))), qualifiers=frozenset()
        )

    if origin is t.Annotated:
        base, *meta = args
        inner = _to_ir(base, env)
        ann = TyAnnoTree(annos=tuple(meta), child=inner.ty.annotations)
        return TyTop(ty=replace(inner.ty, annotations=ann), qualifiers=inner.qualifiers)

    if origin is t.Literal:
        return TyTop(
            ty=TyLiteral(values=tuple(_litval_of(a) for a in args)), qualifiers=frozenset()
        )

    if origin is t.ClassVar:
        (inner,) = args or (t.Any,)
        inner_tt = _to_ir(inner, env)
        return TyTop(ty=inner_tt.ty, qualifiers=inner_tt.qualifiers | {Qualifier.CLASSVAR})

    if origin is t.Final:
        inner = args[0] if args else t.Any
        inner_tt = _to_ir(inner, env)
        return TyTop(ty=inner_tt.ty, qualifiers=inner_tt.qualifiers | {Qualifier.FINAL})

    if origin in (t.Required, t.NotRequired):
        (inner,) = args or (t.Any,)
        inner_tt = _to_ir(inner, env)
        qual = Qualifier.REQUIRED if origin is t.Required else Qualifier.NOTREQUIRED
        return TyTop(ty=inner_tt.ty, qualifiers=inner_tt.qualifiers | {qual})

    if origin is tuple:
        if args and args[-1] is Ellipsis:
            items = tuple(_to_ir(a, env).ty for a in args[:-1]) + (
                TyName(module="builtins", name="Ellipsis"),
            )
            return TyTop(
                ty=TyApp(base=TyName(module="builtins", name="tuple"), args=items),
                qualifiers=frozenset(),
            )
        return TyTop(
            ty=TyTuple(items=tuple(_to_ir(a, env).ty for a in args)), qualifiers=frozenset()
        )

    if origin in (t.Callable, abc.Callable):
        if args and args[0] is Ellipsis:
            return TyTop(
                ty=TyCallable(params=Ellipsis, ret=_to_ir(args[1], env).ty), qualifiers=frozenset()
            )
        if args and isinstance(args[0], (list, tuple)):
            params = tuple(_to_ir(a, env).ty for a in args[0])
            ret = _to_ir(args[1], env).ty
            return TyTop(ty=TyCallable(params=params, ret=ret), qualifiers=frozenset())
        if args:
            return TyTop(
                ty=TyCallable(
                    params=(_to_ir(args[0], env).ty,),
                    ret=_to_ir(args[1], env).ty,
                ),
                qualifiers=frozenset(),
            )
        return TyTop(ty=TyCallable(params=Ellipsis, ret=TyAny()), qualifiers=frozenset())

    if origin is t.Unpack:
        (inner,) = args
        return TyTop(ty=TyUnpack(inner=_to_ir(inner, env).ty), qualifiers=frozenset())

    if getattr(t, "Concatenate", None) is origin:
        return TyTop(
            ty=TyApp(
                base=TyName(module="typing", name="Concatenate"),
                args=tuple(_to_ir(a, env).ty for a in args),
            ),
            qualifiers=frozenset(),
        )

    if origin is type:
        return TyTop(
            ty=TyApp(
                base=TyName(module="builtins", name="type"),
                args=tuple(_to_ir(a, env).ty for a in args),
            ),
            qualifiers=frozenset(),
        )

    if getattr(tp, "__module__", None) == "typing":
        base = _tyname_of(tp)
    else:
        base = _to_ir(origin, env).ty
    return TyTop(
        ty=TyApp(base=base, args=tuple(_to_ir(a, env).ty for a in args)), qualifiers=frozenset()
    )


def parse(tp: object, env: Optional[ParseEnv] = None) -> ParsedTy:
    return ParsedTy(_to_ir(tp, env or ParseEnv()))


# Notes:
#
#     Final, ClassVar, Required, NotRequired are modeled via ``TyTop.qualifiers``.
#
#     Unknown/future typing.Foo[...] falls back to ``TyApp(TyName("typing","Foo"), args_ir)`` — lossless, pass‑through.
#
#     Forward references handled both as strings and ``typing.ForwardRef``.

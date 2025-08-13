from __future__ import annotations

import builtins
from dataclasses import dataclass, field, replace

from .ir import (
    Qualifier,
    Ty,
    TyAny,
    TyApp,
    TyCallable,
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


@dataclass
class EmitCtx:
    """Holds import decisions and name-shortening during emission."""

    # names we need from 'typing' (Annotated, Literal, Callable, ClassVar, Unpack, Any/Never if not builtins in your policy)
    typing_needed: set[str] = field(default_factory=set)
    # If True, emit 'Annotated' not 'typing.Annotated' (and record an import)
    prefer_from_typing: bool = True

    def need(self, *names: str) -> None:
        if self.prefer_from_typing:
            self.typing_needed.update(names)


def emit(t: Ty, ctx: EmitCtx | None = None) -> str:
    ctx = ctx or EmitCtx()
    return _emit(t, ctx)


def emit_top(t: TyTop, ctx: EmitCtx | None = None) -> str:
    ctx = ctx or EmitCtx()
    inner = _emit(t.ty, ctx)
    order = [
        Qualifier.CLASSVAR,
        Qualifier.FINAL,
        Qualifier.REQUIRED,
        Qualifier.NOTREQUIRED,
    ]
    names = {
        Qualifier.CLASSVAR: "ClassVar",
        Qualifier.FINAL: "Final",
        Qualifier.REQUIRED: "Required",
        Qualifier.NOTREQUIRED: "NotRequired",
    }
    for q in order:
        if q in t.qualifiers:
            ctx.need(names[q])
            inner = f"{names[q]}[{inner}]"
    return inner


def _emit(n: Ty, ctx: EmitCtx) -> str:
    if n.annotations:
        nodes = []
        cur = n.annotations
        while cur:
            nodes.append(cur)
            cur = cur.child
        inner = _emit_no_annos(replace(n, annotations=None), ctx)
        for node in reversed(nodes):
            ctx.need("Annotated")
            metas = ", ".join(repr(x) for x in node.annos)
            inner = f"Annotated[{inner}, {metas}]"
        return inner
    return _emit_no_annos(n, ctx)


def _emit_no_annos(n: Ty, ctx: EmitCtx) -> str:
    match n:
        case TyAny():
            # In stubs, 'Any' comes from typing (PEP 484). Import it once.
            ctx.need("Any")
            return "Any"
        case TyNever():
            ctx.need("Never")
            return "Never"

        case TyName(module=None, name=nm):
            return nm
        case TyName(module="builtins", name=nm):
            return nm
        case TyName(module="typing", name=nm):
            # If caller passed e.g. TyName("typing","Type"), you can either keep it qualified
            # or map via prefer_from_typing.
            if ctx.prefer_from_typing:
                ctx.need(nm)
                return nm
            return f"typing.{nm}"
        case TyName(module=m, name=nm):
            return f"{m}.{nm}"

        case TyUnion(options=opts):
            # opts should already be normalized (flat/sorted)
            return " | ".join(_emit(o, ctx) for o in opts)

        case TyApp(base=base, args=args):
            # tuple variadic printed as 'tuple[T, ...]' by virtue of Ellipsis name
            return f"{_emit(base, ctx)}[{', '.join(_emit(a, ctx) for a in args)}]"

        case TyTuple(items=items):
            return f"tuple[{', '.join(_emit(i, ctx) for i in items)}]"

        case TyLiteral(values=vals):
            ctx.need("Literal")
            return f"Literal[{', '.join(repr(v) for v in vals)}]"

        case TyCallable(params=builtins.Ellipsis, ret=r):
            ctx.need("Callable")
            return f"Callable[..., {_emit(r, ctx)}]"
        case TyCallable(params=ps, ret=r):
            ctx.need("Callable")
            params = ", ".join(_emit(p, ctx) for p in ps)
            return f"Callable[[{params}], {_emit(r, ctx)}]"

        case TyUnpack(inner=i):
            ctx.need("Unpack")
            return f"Unpack[{_emit(i, ctx)}]"

        case TyParamSpec(name=n) | TyTypeVar(name=n) | TyTypeVarTuple(name=n):
            # At use-site these print as their bare names.
            return n

        case _:
            raise NotImplementedError(f"Emit not implemented for {type(n).__name__}")

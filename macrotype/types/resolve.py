from __future__ import annotations

from dataclasses import dataclass, replace

from .ir import (
    ParsedTy,
    ResolvedTy,
    Ty,
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

# --------- environment ---------


@dataclass(frozen=True)
class ResolveEnv:
    """
    Context for name resolution.

    imports: mapping from simple name -> fully qualified 'pkg.mod.Name'
      e.g., {"User": "myapp.models.User", "Box": "myapp.types.Box"}
    module: the current module we're resolving within (used only for provenance/error messages for now)
    """

    module: str
    imports: dict[str, str]
    # You can add: globals: dict[str, object] if you decide to eval forward refs later


# --------- implementation ---------


def resolve(t: ParsedTy | Ty, env: ResolveEnv) -> ResolvedTy:
    """Resolve forward refs and qualify bare names. Pure; returns a new tree."""
    top = t if isinstance(t, TyRoot) else TyRoot(ty=t)
    inner = _res(top.ty, env)
    return ResolvedTy(
        TyRoot(
            ty=inner,
            is_final=top.is_final,
            is_required=top.is_required,
            is_classvar=top.is_classvar,
        )
    )


def _res(node: Ty, env: ResolveEnv) -> Ty:
    ann = node.annotations
    match node:
        case TyAny() | TyNever() | TyParamSpec() | TyTypeVar() | TyTypeVarTuple():
            res = node

        case TyName(module=None, name=name):
            if fq := env.imports.get(name):
                mod, _, nm = fq.rpartition(".")
                res = TyName(module=mod, name=nm)
            else:
                res = node

        case TyName(module="typing", name="Type"):
            res = TyName(module="builtins", name="type")

        case TyName():
            res = node

        case TyForward(qualname=qn):
            if fq := env.imports.get(qn):
                mod, _, nm = fq.rpartition(".")
                res = TyName(module=mod, name=nm)
            else:
                res = node  # leave unresolved

        case TyApp(base=base, args=args):
            base_r = _res(base, env)
            args_r = tuple(_res(a, env) for a in args)
            if isinstance(base_r, TyName) and base_r.module == "typing" and base_r.name == "Type":
                base_r = TyName(module="builtins", name="type")
            res = TyApp(base=base_r, args=args_r)

        case TyTuple(items=items):
            res = TyTuple(items=tuple(_res(a, env) for a in items))

        case TyUnion(options=opts):
            res = TyUnion(options=tuple(_res(a, env) for a in opts))

        case TyLiteral():
            res = node

        case TyCallable(params=Ellipsis, ret=ret):
            res = TyCallable(params=Ellipsis, ret=_res(ret, env))

        case TyCallable(params=params, ret=ret):
            res = TyCallable(
                params=tuple(_res(a, env) for a in params),
                ret=_res(ret, env),
            )

        case TyUnpack(inner=inner):
            res = TyUnpack(_res(inner, env))

        case _:
            res = node
    if ann:
        res = replace(res, annotations=ann)
    return res

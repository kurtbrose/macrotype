from __future__ import annotations

from dataclasses import dataclass

from .types_ir import (
    ParsedTy,
    ResolvedTy,
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


def resolve(t: ParsedTy, env: ResolveEnv) -> ResolvedTy:
    """Resolve forward refs and qualify bare names. Pure; returns a new tree."""
    return ResolvedTy(_res(t, env))


def _res(node: Ty, env: ResolveEnv) -> Ty:
    match node:
        case TyAny() | TyNever() | TyParamSpec() | TyTypeVar() | TyTypeVarTuple():
            return node

        case TyName(module=None, name=name):
            if fq := env.imports.get(name):
                mod, _, nm = fq.rpartition(".")
                return TyName(module=mod, name=nm)
            return node

        case TyName(module="typing", name="Type"):
            return TyName(module="builtins", name="type")

        case TyName():
            return node

        case TyForward(qualname=qn):
            if fq := env.imports.get(qn):
                mod, _, nm = fq.rpartition(".")
                return TyName(module=mod, name=nm)
            return node  # leave unresolved

        case TyApp(base=base, args=args):
            base_r = _res(base, env)
            args_r = tuple(_res(a, env) for a in args)
            if isinstance(base_r, TyName) and base_r.module == "typing" and base_r.name == "Type":
                base_r = TyName(module="builtins", name="type")
            return TyApp(base=base_r, args=args_r)

        case TyTuple(items=items):
            return TyTuple(items=tuple(_res(a, env) for a in items))

        case TyUnion(options=opts):
            return TyUnion(options=tuple(_res(a, env) for a in opts))

        case TyLiteral():
            return node

        case TyAnnotated(base=base, anno=anno):
            return TyAnnotated(base=_res(base, env), anno=anno)

        case TyCallable(params=Ellipsis, ret=ret):
            return TyCallable(params=Ellipsis, ret=_res(ret, env))

        case TyCallable(params=params, ret=ret):
            return TyCallable(
                params=tuple(_res(a, env) for a in params),
                ret=_res(ret, env),
            )

        case TyClassVar(inner=inner):
            return TyClassVar(_res(inner, env))

        case TyUnpack(inner=inner):
            return TyUnpack(_res(inner, env))

        case _:
            return node

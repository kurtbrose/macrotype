from __future__ import annotations

from dataclasses import dataclass

from .types_ir import (
    NormalizedTy,
    ResolvedTy,
    Ty,
    TyAnnotated,
    TyAny,
    TyApp,
    TyCallable,
    TyClassVar,
    TyLiteral,
    TyName,
    TyNever,
    TyTuple,
    TyUnion,
    TyUnpack,
)


@dataclass(frozen=True)
class NormOpts:
    """Options controlling normalization behaviour."""

    # drop Annotated around Any (common cleanup)
    drop_annotated_any: bool = True
    # canonicalize typing collections to builtins (List->list, etc.)
    typing_to_builtins: bool = True
    # sort union options deterministically by their emitted-ish key
    sort_unions: bool = True
    # dedup union options structurally
    dedup_unions: bool = True


_DEFAULT = NormOpts()

_TYPING_TO_BUILTINS = {
    ("typing", "List"): ("builtins", "list"),
    ("typing", "Dict"): ("builtins", "dict"),
    ("typing", "Tuple"): ("builtins", "tuple"),
    ("typing", "Set"): ("builtins", "set"),
    ("typing", "FrozenSet"): ("builtins", "frozenset"),
    ("typing", "Type"): ("builtins", "type"),
}


def norm(t: ResolvedTy, opts: NormOpts | None = None) -> NormalizedTy:
    """Normalize *t* according to *opts*."""

    return NormalizedTy(_norm(t, opts or _DEFAULT))


def _norm(n: Ty, o: NormOpts) -> Ty:
    match n:
        case TyAny() | TyNever():
            return n

        case TyName(module=mod, name=name):
            if o.typing_to_builtins:
                key = (mod, name)
                if key in _TYPING_TO_BUILTINS:
                    m, k = _TYPING_TO_BUILTINS[key]
                    return TyName(module=m, name=k)
            return n

        case TyApp(base=base, args=args):
            base_r = _norm(base, o)
            args_r = tuple(_norm(a, o) for a in args)
            # Variadic tuple canonical shape: base must be builtins.tuple, last arg Ellipsis => leave as-is
            return TyApp(base=base_r, args=args_r)

        case TyTuple(items=items):
            return TyTuple(items=tuple(_norm(a, o) for a in items))

        case TyUnion(options=opts):
            # flatten
            flat: list[Ty] = []
            for x in opts:
                x = _norm(x, o)
                if isinstance(x, TyUnion):
                    flat.extend(x.options)
                else:
                    flat.append(x)

            # dedup by a structural key
            if o.dedup_unions:
                seen: set[str] = set()
                uniq: list[Ty] = []
                for x in flat:
                    k = _key(x)
                    if k not in seen:
                        seen.add(k)
                        uniq.append(x)
                flat = uniq

            if o.sort_unions:
                flat = sorted(flat, key=_key)

            if not flat:
                return TyNever()  # Union[] → bottom (policy; rarely occurs)
            if len(flat) == 1:
                return flat[0]
            return TyUnion(options=tuple(flat))

        case TyLiteral(values=vals):
            # optional dedup/ordering (stable by repr key)
            seen = set()
            out = []
            for v in vals:
                r = repr(v)
                if r not in seen:
                    seen.add(r)
                    out.append(v)
            return TyLiteral(values=tuple(out))

        case TyAnnotated(base=base, anno=anno):
            base_n = _norm(base, o)
            if o.drop_annotated_any and isinstance(base_n, TyAny):
                return base_n
            # merge nested Annotated: Annotated[Annotated[T, a], b] -> Annotated[T, a, b]
            if isinstance(base_n, TyAnnotated):
                return TyAnnotated(base=base_n.base, anno=base_n.anno + anno)
            return TyAnnotated(base=base_n, anno=anno)

        case TyCallable(params=Ellipsis, ret=ret):
            return TyCallable(params=Ellipsis, ret=_norm(ret, o))

        case TyCallable(params=params, ret=ret):
            return TyCallable(
                params=tuple(_norm(a, o) for a in params),
                ret=_norm(ret, o),
            )

        case TyClassVar(inner=inner):
            return TyClassVar(inner=_norm(inner, o))

        case TyUnpack(inner=inner):
            return TyUnpack(inner=_norm(inner, o))

        case _:
            return n


def _key(n: Ty) -> str:
    """Deterministic structural key for sorting/dedup. Keep simple (repr-based) to start."""

    return repr(n)

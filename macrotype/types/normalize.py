from __future__ import annotations

import typing as t
from dataclasses import dataclass, replace

from .ir import (
    NormalizedTy,
    ResolvedTy,
    Ty,
    TyAny,
    TyApp,
    TyCallable,
    TyLiteral,
    TyNever,
    TyRoot,
    TyType,
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
    t.List: list,
    t.Dict: dict,
    t.Tuple: tuple,
    t.Set: set,
    t.FrozenSet: frozenset,
    t.Type: type,
}


def norm(t: ResolvedTy | Ty, opts: NormOpts | None = None) -> NormalizedTy:
    """Normalize *t* according to *opts*."""

    top = t if isinstance(t, TyRoot) else TyRoot(ty=t)
    inner = _norm(top.ty, opts or _DEFAULT) if top.ty is not None else None
    return NormalizedTy(
        TyRoot(
            ty=inner,
            annotations=top.annotations,
            is_final=top.is_final,
            is_required=top.is_required,
            is_classvar=top.is_classvar,
        )
    )


def _norm(n: Ty | None, o: NormOpts) -> Ty | None:
    if n is None:
        return None
    ann = n.annotations
    if ann and o.drop_annotated_any and isinstance(n, TyAny):
        return TyAny()
    match n:
        case TyAny() | TyNever():
            res = n

        case TyType(type_=tp):
            if o.typing_to_builtins and tp in _TYPING_TO_BUILTINS:
                return TyType(type_=_TYPING_TO_BUILTINS[tp])
            res = n

        case TyApp(base=base, args=args):
            base_r = _norm(base, o)
            args_r = tuple(_norm(a, o) for a in args)
            # Variadic tuple canonical shape: base must be builtins.tuple, last arg Ellipsis => leave as-is
            res = TyApp(base=base_r, args=args_r)

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
                res = TyNever()  # Union[] → bottom (policy; rarely occurs)
            elif len(flat) == 1:
                res = flat[0]
            else:
                res = TyUnion(options=tuple(flat))

        case TyLiteral(values=vals):
            # optional dedup/ordering (stable by repr key)
            seen = set()
            out = []
            for v in vals:
                r = repr(v)
                if r not in seen:
                    seen.add(r)
                    out.append(v)
            res = TyLiteral(values=tuple(out))

        case TyCallable(params=Ellipsis, ret=ret):
            res = TyCallable(params=Ellipsis, ret=_norm(ret, o))

        case TyCallable(params=params, ret=ret):
            res = TyCallable(
                params=tuple(_norm(a, o) for a in params),
                ret=_norm(ret, o),
            )

        case TyUnpack(inner=inner):
            res = TyUnpack(inner=_norm(inner, o))

        case _:
            res = n
    if ann:
        res = replace(res, annotations=ann)
    return res


def _key(n: Ty) -> str:
    """Deterministic structural key for sorting/dedup. Keep simple (repr-based) to start."""

    return repr(n)

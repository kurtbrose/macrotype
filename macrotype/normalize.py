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
    # Leaves
    if isinstance(n, (TyAny, TyNever)):
        return n

    if isinstance(n, TyName):
        if o.typing_to_builtins:
            key = (n.module, n.name)
            if key in _TYPING_TO_BUILTINS:
                mod, nm = _TYPING_TO_BUILTINS[key]
                return TyName(module=mod, name=nm)
        return n

    if isinstance(n, TyApp):
        base = _norm(n.base, o)
        args = tuple(_norm(a, o) for a in n.args)

        # Variadic tuple canonical shape: base must be builtins.tuple, last arg Ellipsis => leave as-is
        return TyApp(base=base, args=args)

    if isinstance(n, TyTuple):
        return TyTuple(items=tuple(_norm(a, o) for a in n.items))

    if isinstance(n, TyUnion):
        # flatten
        flat: list[Ty] = []
        for x in n.options:
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

    if isinstance(n, TyLiteral):
        # optional dedup/ordering (stable by repr key)
        vals = n.values
        # dedup preserving first occurrence
        seen = set()
        out = []
        for v in vals:
            r = repr(v)
            if r not in seen:
                seen.add(r)
                out.append(v)
        return TyLiteral(values=tuple(out))

    if isinstance(n, TyAnnotated):
        base = _norm(n.base, o)
        if o.drop_annotated_any and isinstance(base, TyAny):
            return base
        # merge nested Annotated: Annotated[Annotated[T, a], b] -> Annotated[T, a, b]
        if isinstance(base, TyAnnotated):
            return TyAnnotated(base=base.base, anno=base.anno + n.anno)
        return TyAnnotated(base=base, anno=n.anno)

    if isinstance(n, TyCallable):
        if n.params is Ellipsis:
            return TyCallable(params=Ellipsis, ret=_norm(n.ret, o))
        return TyCallable(params=tuple(_norm(a, o) for a in n.params), ret=_norm(n.ret, o))

    if isinstance(n, TyClassVar):
        return TyClassVar(inner=_norm(n.inner, o))

    if isinstance(n, TyUnpack):
        return TyUnpack(inner=_norm(n.inner, o))

    # Default: return as-is
    return n


def _key(n: Ty) -> str:
    """Deterministic structural key for sorting/dedup. Keep simple (repr-based) to start."""

    return repr(n)

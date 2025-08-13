from __future__ import annotations

import typing as t
from dataclasses import replace
from types import EllipsisType
from typing import Any

from .ir import (
    Ty,
    TyAny,
    TyApp,
    TyCallable,
    TyForward,
    TyLiteral,
    TyNever,
    TyParamSpec,
    TyRoot,
    TyType,
    TyTypeVar,
    TyTypeVarTuple,
    TyUnion,
    TyUnpack,
)


def unparse(t: Ty) -> Any:
    """Convert a :class:`Ty` back into a Python typing object."""
    return _unparse(t)


def unparse_top(root: TyRoot) -> Any:
    """Convert a :class:`TyRoot` back into a Python typing object."""
    inner = None if root.ty is None else _unparse(root.ty)
    if root.annotations and inner is not None:
        inner = _apply_annos(inner, root.annotations)
    res = inner
    if root.is_classvar and res is not None:
        res = t.ClassVar[res]
    if root.is_final:
        res = t.Final if res is None else t.Final[res]
    if root.is_required is True and res is not None:
        res = t.Required[res]
    elif root.is_required is False and res is not None:
        res = t.NotRequired[res]
    return res


def _apply_annos(inner: Any, tree) -> Any:
    node = tree
    out = inner
    while node:
        out = t.Annotated.__class_getitem__((out, *node.annos))
        node = node.child
    return out


def _unparse(n: Ty) -> Any:
    if n.annotations:
        inner = _unparse_no_annos(replace(n, annotations=None))
        return _apply_annos(inner, n.annotations)
    return _unparse_no_annos(n)


def _unparse_no_annos(n: Ty) -> Any:
    match n:
        case TyAny():
            return t.Any
        case TyNever():
            return t.Never
        case TyType(type_=tp):
            if tp is EllipsisType:
                return ...
            return tp
        case TyUnion(options=opts):
            objs = [_unparse(o) for o in opts]
            it = iter(objs)
            res = next(it)
            for o in it:
                res = res | o
            return res
        case TyApp(base=base, args=args):
            b = _unparse(base)
            a_objs = tuple(_unparse(a) for a in args)
            if len(a_objs) == 1:
                return b[a_objs[0]]
            return b[a_objs]
        case TyLiteral(values=vals):
            return t.Literal[vals]
        case TyCallable(params=ps, ret=r):
            if ps is Ellipsis:
                return t.Callable[..., _unparse(r)]
            params_list = [_unparse(p) for p in ps]
            return t.Callable[params_list, _unparse(r)]
        case TyUnpack(inner=i):
            return t.Unpack[_unparse(i)]
        case TyParamSpec(name=n):
            return t.ParamSpec(n)
        case TyTypeVar(name=n, bound=b, constraints=cs, cov=cv, contrav=cn):
            bound_obj = _unparse(b) if b else None
            constr_objs = tuple(_unparse(c) for c in cs)
            return t.TypeVar(n, *constr_objs, bound=bound_obj, covariant=cv, contravariant=cn)
        case TyTypeVarTuple(name=n):
            return t.TypeVarTuple(n)
        case TyForward(qualname=q):
            return t.ForwardRef(q)
        case _:
            raise NotImplementedError(f"Unparse not implemented for {type(n).__name__}")

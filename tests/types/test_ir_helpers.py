from __future__ import annotations

from macrotype.types.ir import (
    Ty,
    TyApp,
    TyType,
    TyUnion,
    has_type_member,
    strip_type_members,
)


def t_int() -> Ty:
    return TyType(type_=int)


def t_none() -> Ty:
    return TyType(type_=type(None))


def t_list(elem: Ty) -> Ty:
    return TyApp(base=TyType(type_=list), args=(elem,))


def t_dict(key: Ty, val: Ty) -> Ty:
    return TyApp(base=TyType(type_=dict), args=(key, val))


# ---------- TyType -----------------------------------------------------------


def test_tytype_basic() -> None:
    t = t_int()
    assert t.base_type is int
    assert t.generic_args == ()
    assert t.union_types == (t,)
    assert not t.is_generic


# ---------- TyApp ------------------------------------------------------------


def test_list_generic() -> None:
    inner = t_int()
    lst = t_list(inner)

    assert lst.is_generic
    assert lst.base_type is list
    assert lst.generic_args == (inner,)


def test_nested_list() -> None:
    inner = t_list(t_int())
    outer = t_list(inner)

    assert outer.base_type is list
    assert outer.generic_args[0].base_type is list
    assert outer.generic_args[0].generic_args == (t_int(),)


def test_dict_generic() -> None:
    d = t_dict(TyType(type_=str), t_int())

    assert d.is_generic
    assert d.base_type is dict
    key_ty, val_ty = d.generic_args
    assert key_ty.base_type is str
    assert val_ty.base_type is int


# ---------- TyUnion ----------------------------------------------------------


def test_union_properties() -> None:
    u = TyUnion(options=(t_int(), t_none()))

    assert u.union_types == (t_int(), t_none())
    assert u.base_type is None  # unions have no constructor
    assert not u.is_generic


# ---------- helper functions -------------------------------------------------


def test_has_and_strip_helpers() -> None:
    u = TyUnion(options=(t_int(), t_none()))
    assert has_type_member(u, {type(None)})
    stripped = strip_type_members(u, {type(None)})
    assert stripped.base_type is int
    assert stripped.union_types == (t_int(),)

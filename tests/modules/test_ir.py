from __future__ import annotations

import importlib
import types
import typing

import pytest

from macrotype.modules import from_module
from macrotype.modules.ir import (
    ClassDecl,
    Decl,
    FuncDecl,
    ModuleDecl,
    TypeDefDecl,
    VarDecl,
)
from macrotype.modules.scanner import scan_module
from macrotype.modules.transformers import canonicalize_foreign_symbols, expand_overloads


@pytest.fixture(scope="module")
def idx() -> dict[str, object]:
    ann = importlib.import_module("tests.annotations")
    ann_new = importlib.import_module("tests.annotations_new")
    for name in dir(ann_new):
        if name.startswith("__"):
            continue
        setattr(ann, name, getattr(ann_new, name))
    ann.__annotations__ |= ann_new.__annotations__
    mi = scan_module(ann)
    assert isinstance(mi, ModuleDecl)
    assert mi.obj is ann
    by_key: dict[str, Decl] = {s.name: s for s in mi.members}
    by_name: dict[str, list[Decl]] = {}
    for s in mi.members:
        by_name.setdefault(s.name, []).append(s)
    return {"by_key": by_key, "by_name": by_name, "all": mi.members}


def get(idx: dict[str, object], key: str) -> Decl:
    return typing.cast(Decl, idx["by_key"][key])


def test_module_var_and_func(idx: dict[str, object]) -> None:
    x = get(idx, "GLOBAL")
    assert isinstance(x, VarDecl)
    assert x.site.annotation is int

    f = get(idx, "mult")
    assert isinstance(f, FuncDecl)
    names = [p.name for p in f.params]
    assert "b" not in names


def test_basic_class_members(idx: dict[str, object]) -> None:
    c = get(idx, "Basic")
    assert isinstance(c, ClassDecl)
    member_names = [m.name for m in c.members]
    assert {"Nested", "copy", "prop"} <= set(member_names)


def test_typeddict_fields(idx: dict[str, object]) -> None:
    td = get(idx, "SampleDict")
    assert isinstance(td, ClassDecl)
    assert td.is_typeddict is True
    fields = [f.name for f in td.td_fields]
    assert fields == ["name", "age"]


def test_aliases() -> None:
    ann = importlib.import_module("tests.annotations_new")
    mi = scan_module(ann)
    canonicalize_foreign_symbols(mi)
    by_key = {s.name: s for s in mi.members}

    other = typing.cast(TypeDefDecl, by_key["Other"])
    assert isinstance(other, TypeDefDecl)
    assert typing.get_origin(other.value.annotation) is dict

    mylist = typing.cast(TypeDefDecl, by_key["MyList"])
    assert isinstance(mylist, TypeDefDecl)
    assert typing.get_origin(mylist.value.annotation) is list


def test_function_sites(idx: dict[str, object]) -> None:
    f = get(idx, "annotated_fn")
    assert isinstance(f, FuncDecl)
    ps = f.params
    assert len(ps) == 1

    def unwrap(tp: object) -> object:
        while typing.get_origin(tp) is typing.Annotated:
            tp = typing.get_args(tp)[0]
        return typing.get_origin(tp) or tp

    assert unwrap(ps[0].annotation) is int
    assert f.ret and unwrap(f.ret.annotation) is str


def test_nested_classes(idx: dict[str, object]) -> None:
    outer = get(idx, "Outer")
    assert isinstance(outer, ClassDecl)
    names = [m.name for m in outer.members]
    assert "Inner" in names


def test_overloads_present(idx: dict[str, object]) -> None:
    over = get(idx, "over")
    assert isinstance(over, FuncDecl)
    assert over.ret is not None


def test_async_functions(idx: dict[str, object]) -> None:
    af = get(idx, "async_add_one")
    assert isinstance(af, FuncDecl)
    assert af.ret and af.ret.annotation is int


def test_properties_detected_as_functions_or_vars(idx: dict[str, object]) -> None:
    w = get(idx, "WrappedDescriptors")
    assert isinstance(w, ClassDecl)
    members = {m.name for m in w.members}
    assert {"wrapped_prop", "wrapped_static", "wrapped_cls"} <= members


def test_variadic_things_dont_crash(idx: dict[str, object]) -> None:
    vnt = get(idx, "VarNamedTuple")
    assert isinstance(vnt, ClassDecl)


def test_simple_alias_to_foreign() -> None:
    ann = importlib.import_module("tests.annotations")
    mi = scan_module(ann)
    canonicalize_foreign_symbols(mi)
    by_key = {s.name: s for s in mi.members}

    sin = by_key["SIN_ALIAS"]
    assert isinstance(sin, TypeDefDecl)

    cos = by_key["COS_VAR"]
    assert isinstance(cos, VarDecl)


def test_class_vars_scanned(idx: dict[str, object]) -> None:
    cv = get(idx, "ClassVarExample")
    assert isinstance(cv, ClassDecl)
    names = [m.name for m in cv.members]
    assert "y" in names


def test_td_inheritance(idx: dict[str, object]) -> None:
    sub = get(idx, "SubTD")
    assert isinstance(sub, ClassDecl)
    assert any(b.role == "base" for b in sub.bases)


def test_dataclass_transform() -> None:
    ann = importlib.import_module("tests.annotations")
    mi = from_module(ann)
    frozen = next(s for s in mi.members if s.name == "Frozen")
    assert isinstance(frozen, ClassDecl)
    assert "dataclass(frozen=True, slots=True)" in frozen.decorators
    member_names = {m.name for m in frozen.members}
    assert "__init__" not in member_names

    nae = next(s for s in mi.members if s.name == "NoAutoEq")
    assert isinstance(nae, ClassDecl)
    assert "__eq__" in {m.name for m in nae.members}


def test_expand_overloads_transform() -> None:
    ann = importlib.import_module("tests.annotations")
    ann_new = importlib.import_module("tests.annotations_new")
    ann.special_neg = ann_new.special_neg
    mi = scan_module(ann)
    expand_overloads(mi)

    overs = [s for s in mi.members if s.name == "over"]
    assert len(overs) == 2
    assert all("overload" in s.decorators for s in overs)

    specials = [s for s in mi.members if s.name == "special_neg"]
    assert len(specials) == 3
    assert specials[-1].params[0].annotation is int

    mixed = [s for s in mi.members if s.name == "mixed_overload"]
    assert len(mixed) == 3
    assert mixed[-1].params[0].annotation == (int | str)


def test_get_all_decls_includes_nested() -> None:
    ann = importlib.import_module("tests.annotations")
    mi = scan_module(ann)
    names = {s.name for s in mi.get_all_decls()}
    assert "Nested" in names


def test_flag_transform() -> None:
    ann = importlib.import_module("tests.annotations")
    mi = from_module(ann)

    fc = next(s for s in mi.members if s.name == "FinalClass")
    assert isinstance(fc, ClassDecl)
    assert fc.flags.get("final") is True

    hfm = next(s for s in mi.members if s.name == "HasFinalMethod")
    assert isinstance(hfm, ClassDecl)
    fm = next(m for m in hfm.members if isinstance(m, FuncDecl) and m.name == "do_final")
    assert fm.flags.get("final") is True
    assert "final" in fm.decorators

    ff = next(s for s in mi.members if s.name == "final_func")
    assert isinstance(ff, FuncDecl)
    assert ff.flags.get("final") is True
    assert "final" not in ff.decorators

    ann_new = importlib.import_module("tests.annotations_new")
    mi_new = from_module(ann_new)
    ol = next(s for s in mi_new.members if s.name == "OverrideLate")
    assert isinstance(ol, ClassDecl)
    cls_override = next(
        m for m in ol.members if isinstance(m, FuncDecl) and m.name == "cls_override"
    )
    assert cls_override.flags.get("override") is True
    assert "override" in cls_override.decorators

    ab = next(s for s in mi.members if s.name == "AbstractBase")
    assert isinstance(ab, ClassDecl)
    assert ab.flags.get("abstract") is True
    m = next(m for m in ab.members if isinstance(m, FuncDecl) and m.name == "do_something")
    assert m.flags.get("abstract") is True
    assert "abstractmethod" in m.decorators


def test_strict_mode_normalizes_union() -> None:
    ann = importlib.import_module("tests.strict_union")

    mi_default = from_module(ann)
    var_default = next(
        s for s in mi_default.members if isinstance(s, VarDecl) and s.name == "STRICT_UNION"
    )
    assert typing.get_origin(var_default.site.annotation) is typing.Union

    mi_strict = from_module(ann, strict=True)
    var_strict = next(
        s for s in mi_strict.members if isinstance(s, VarDecl) and s.name == "STRICT_UNION"
    )
    assert var_strict.site.annotation == (int | str)
    assert typing.get_origin(var_strict.site.annotation) is types.UnionType


def test_strict_mode_raises_on_invalid_annotation() -> None:
    mod = importlib.import_module("tests.strict_error")
    with pytest.raises(TypeError):
        from_module(mod, strict=True)

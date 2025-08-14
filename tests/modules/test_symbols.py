from __future__ import annotations

import importlib
import typing

import pytest

from macrotype.modules import from_module
from macrotype.modules.scanner import ModuleInfo, scan_module
from macrotype.modules.symbols import (
    AliasSymbol,
    ClassSymbol,
    FuncSymbol,
    Symbol,
    VarSymbol,
)
from macrotype.modules.transformers import canonicalize_foreign_symbols, expand_overloads


@pytest.fixture(scope="module")
def idx() -> dict[str, object]:
    ann = importlib.import_module("tests.annotations")
    mi = scan_module(ann)
    assert isinstance(mi, ModuleInfo)
    assert mi.mod is ann
    by_key: dict[str, Symbol] = {s.name: s for s in mi.symbols}
    by_name: dict[str, list[Symbol]] = {}
    for s in mi.symbols:
        by_name.setdefault(s.name, []).append(s)
    return {"by_key": by_key, "by_name": by_name, "all": mi.symbols}


def get(idx: dict[str, object], key: str) -> Symbol:
    return typing.cast(Symbol, idx["by_key"][key])


def test_module_var_and_func(idx: dict[str, object]) -> None:
    x = get(idx, "GLOBAL")
    assert isinstance(x, VarSymbol)
    assert x.site.annotation is int

    f = get(idx, "mult")
    assert isinstance(f, FuncSymbol)
    names = [p.name for p in f.params]
    assert "b" not in names


def test_basic_class_members(idx: dict[str, object]) -> None:
    c = get(idx, "Basic")
    assert isinstance(c, ClassSymbol)
    member_names = [m.name for m in c.members]
    assert {"Nested", "copy", "prop"} <= set(member_names)


def test_typeddict_fields(idx: dict[str, object]) -> None:
    td = get(idx, "SampleDict")
    assert isinstance(td, ClassSymbol)
    assert td.is_typeddict is True
    fields = [f.name for f in td.td_fields]
    assert fields == ["name", "age"]


def test_aliases() -> None:
    ann = importlib.import_module("tests.annotations")
    mi = scan_module(ann)
    canonicalize_foreign_symbols(mi)
    by_key = {s.name: s for s in mi.symbols}

    other = typing.cast(AliasSymbol, by_key["Other"])
    assert isinstance(other, AliasSymbol)
    assert typing.get_origin(other.value.annotation) is dict

    mylist = typing.cast(AliasSymbol, by_key["MyList"])
    assert isinstance(mylist, AliasSymbol)
    assert typing.get_origin(mylist.value.annotation) is list


def test_function_sites(idx: dict[str, object]) -> None:
    f = get(idx, "annotated_fn")
    assert isinstance(f, FuncSymbol)
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
    assert isinstance(outer, ClassSymbol)
    names = [m.name for m in outer.members]
    assert "Inner" in names


def test_overloads_present(idx: dict[str, object]) -> None:
    over = get(idx, "over")
    assert isinstance(over, FuncSymbol)
    assert over.ret is not None


def test_async_functions(idx: dict[str, object]) -> None:
    af = get(idx, "async_add_one")
    assert isinstance(af, FuncSymbol)
    assert af.ret and af.ret.annotation is int


def test_properties_detected_as_functions_or_vars(idx: dict[str, object]) -> None:
    w = get(idx, "WrappedDescriptors")
    assert isinstance(w, ClassSymbol)
    members = {m.name for m in w.members}
    assert {"wrapped_prop", "wrapped_static", "wrapped_cls"} <= members


def test_variadic_things_dont_crash(idx: dict[str, object]) -> None:
    vnt = get(idx, "VarNamedTuple")
    assert isinstance(vnt, ClassSymbol)


def test_simple_alias_to_foreign() -> None:
    ann = importlib.import_module("tests.annotations")
    mi = scan_module(ann)
    canonicalize_foreign_symbols(mi)
    by_key = {s.name: s for s in mi.symbols}

    sin = by_key["SIN_ALIAS"]
    assert isinstance(sin, AliasSymbol)

    cos = by_key["COS_VAR"]
    assert isinstance(cos, VarSymbol)


def test_class_vars_scanned(idx: dict[str, object]) -> None:
    cv = get(idx, "ClassVarExample")
    assert isinstance(cv, ClassSymbol)
    names = [m.name for m in cv.members]
    assert "y" in names


def test_td_inheritance(idx: dict[str, object]) -> None:
    sub = get(idx, "SubTD")
    assert isinstance(sub, ClassSymbol)
    assert any(b.role == "base" for b in sub.bases)


def test_dataclass_transform() -> None:
    ann = importlib.import_module("tests.annotations")
    mi = from_module(ann)
    frozen = next(s for s in mi.symbols if s.name == "Frozen")
    assert isinstance(frozen, ClassSymbol)
    assert "dataclass(frozen=True, slots=True)" in frozen.decorators
    member_names = {m.name for m in frozen.members}
    assert "__init__" not in member_names

    nae = next(s for s in mi.symbols if s.name == "NoAutoEq")
    assert isinstance(nae, ClassSymbol)
    assert "__eq__" in {m.name for m in nae.members}


def test_expand_overloads_transform() -> None:
    ann = importlib.import_module("tests.annotations")
    mi = scan_module(ann)
    expand_overloads(mi)

    overs = [s for s in mi.symbols if s.name == "over"]
    assert len(overs) == 2
    assert all("overload" in s.decorators for s in overs)

    specials = [s for s in mi.symbols if s.name == "special_neg"]
    assert len(specials) == 3
    assert specials[-1].params[0].annotation is int

    mixed = [s for s in mi.symbols if s.name == "mixed_overload"]
    assert len(mixed) == 3
    assert mixed[-1].params[0].annotation == (int | str)


def test_flag_transform() -> None:
    ann = importlib.import_module("tests.annotations")
    mi = from_module(ann)

    fc = next(s for s in mi.symbols if s.name == "FinalClass")
    assert isinstance(fc, ClassSymbol)
    assert fc.flags.get("final") is True

    hfm = next(s for s in mi.symbols if s.name == "HasFinalMethod")
    assert isinstance(hfm, ClassSymbol)
    fm = next(m for m in hfm.members if isinstance(m, FuncSymbol) and m.name == "do_final")
    assert fm.flags.get("final") is True
    assert "final" in fm.decorators

    ff = next(s for s in mi.symbols if s.name == "final_func")
    assert isinstance(ff, FuncSymbol)
    assert ff.flags.get("final") is True
    assert "final" not in ff.decorators

    ol = next(s for s in mi.symbols if s.name == "OverrideLate")
    assert isinstance(ol, ClassSymbol)
    cls_override = next(
        m for m in ol.members if isinstance(m, FuncSymbol) and m.name == "cls_override"
    )
    assert cls_override.flags.get("override") is True
    assert "override" in cls_override.decorators

    ab = next(s for s in mi.symbols if s.name == "AbstractBase")
    assert isinstance(ab, ClassSymbol)
    assert ab.flags.get("abstract") is True
    m = next(m for m in ab.members if isinstance(m, FuncSymbol) and m.name == "do_something")
    assert m.flags.get("abstract") is True
    assert "abstractmethod" in m.decorators

from __future__ import annotations

import importlib

import pytest

from macrotype.modules.scanner import ModuleInfo, scan_module
from macrotype.modules.symbols import AliasSymbol, ClassSymbol, FuncSymbol, Site, Symbol, VarSymbol

# ---- normalize to stable “shapes” (ignores file/line etc.) ----


def site_shape(s: Site) -> dict:
    return {
        "role": s.role,
        "name": s.name,
        "index": s.index,
        "raw": _raw_sig(s.raw),  # compact, comparable
    }


def _raw_sig(obj: object) -> str:
    # keep this simple & consistent across Py versions
    try:
        import typing as _t

        origin = getattr(_t, "get_origin")(obj)
        args = getattr(_t, "get_args")(obj)
        if origin is _t.Annotated:
            return _raw_sig(args[0])
        if origin:
            return f"{getattr(origin, '__name__', repr(origin))}[{', '.join(map(_raw_sig, args))}]"
        if isinstance(obj, type):
            return f"{getattr(obj, '__module__', '')}.{obj.__name__}"
        return repr(obj)
    except Exception:
        return repr(obj)


def sym_shape(sym: Symbol) -> dict:
    base = {"kind": type(sym).__name__, "name": sym.name, "key": sym.key}
    match sym:
        case VarSymbol(site=site):
            base["site"] = site_shape(site)
        case FuncSymbol(params=ps, ret=rt):
            base["params"] = [site_shape(p) for p in ps]
            base["ret"] = site_shape(rt) if rt else None
            base["decorators"] = list(getattr(sym, "decorators", ()))
        case ClassSymbol(bases=bs, td_fields=fs, is_typeddict=is_td, td_total=tot, members=mems):
            base["bases"] = [site_shape(b) for b in bs]
            base["td_fields"] = [site_shape(f) for f in fs]
            base["is_typeddict"] = is_td
            base["td_total"] = tot
            base["members"] = sorted([(m.name, type(m).__name__) for m in mems])
        case AliasSymbol(value=v):
            base["value"] = site_shape(v) if v else None
    return base


# ---- one-time module scan as a fixture ----


@pytest.fixture(scope="module")
def idx():
    ann = importlib.import_module("tests.annotations")  # your big fixture module
    mi = scan_module(ann)
    assert isinstance(mi, ModuleInfo)
    assert mi.mod is ann
    assert mi.provenance == "tests.annotations"
    shapes = [sym_shape(s) for s in mi.symbols]
    # index by key and name for convenience
    by_key = {s["key"]: s for s in shapes}
    by_name = {}
    for s in shapes:
        by_name.setdefault(s["name"], []).append(s)
    return {"by_key": by_key, "by_name": by_name, "all": shapes}


def get(idx, key: str) -> dict:
    return idx["by_key"][key]


# --------------------------------------------------------------------------
# Now the fun part: MANY tiny, readable assertions
# --------------------------------------------------------------------------


def test_module_var_and_func(idx):
    X = get(idx, "tests.annotations.GLOBAL")
    assert X["kind"] == "VarSymbol"
    assert X["site"]["raw"] in {"int", "builtins.int"}  # relaxed

    f = get(idx, "tests.annotations.mult")
    assert f["kind"] == "FuncSymbol"
    # Only annotated params become sites; ‘a’ is unannotated in your code
    names = [p["name"] for p in f["params"]]
    assert "b" not in names  # default but unannotated


def test_basic_class_members(idx):
    C = get(idx, "tests.annotations.Basic")
    assert C["kind"] == "ClassSymbol"
    # has nested members: property, methods, nested class
    member_names = [n for (n, _k) in C["members"]]
    assert {"Nested", "copy", "prop"} <= set(member_names)


def test_typeddict_fields(idx):
    TD = get(idx, "tests.annotations.SampleDict")
    assert TD["is_typeddict"] is True
    fields = [f["name"] for f in TD["td_fields"]]
    assert fields == ["name", "age"]


def test_aliases(idx):
    other = get(idx, "tests.annotations.Other")
    assert other["kind"] == "AliasSymbol"
    assert "dict" in other["value"]["raw"]

    mylist = get(idx, "tests.annotations.MyList")
    assert mylist["kind"] == "AliasSymbol"
    assert "list" in mylist["value"]["raw"]


def test_function_sites(idx):
    f = get(idx, "tests.annotations.annotated_fn")
    ps = f["params"]
    assert len(ps) == 1
    assert ps[0]["raw"] in {"int", "builtins.int"}
    assert f["ret"]["raw"] in {"str", "builtins.str"}


def test_nested_classes(idx):
    Outer = get(idx, "tests.annotations.Outer")
    names = [n for (n, _k) in Outer["members"]]
    assert "Inner" in names


def test_overloads_present(idx):
    # We just see the function symbol; overload grouping can be later
    over = get(idx, "tests.annotations.over")
    assert over["kind"] == "FuncSymbol"
    # You can assert #params/ret sites from annotations: 1 ret
    assert over["ret"] is not None


def test_async_functions(idx):
    af = get(idx, "tests.annotations.async_add_one")
    assert af["kind"] == "FuncSymbol"
    assert af["ret"]["raw"] in {"int", "builtins.int"}


def test_properties_detected_as_functions_or_vars(idx):
    # At scan stage we treat decorators later; here we just ensure function symbol exists
    w = get(idx, "tests.annotations.WrappedDescriptors")
    members = dict(w["members"])
    assert "wrapped_prop" in members
    assert "wrapped_static" in members
    assert "wrapped_cls" in members


def test_variadic_things_dont_crash(idx):
    vnt = get(idx, "tests.annotations.VarNamedTuple")
    assert vnt["kind"] == "ClassSymbol"
    # not asserting exact shape; scan shouldn’t crash


def test_simple_alias_to_foreign(idx):
    sin = get(idx, "tests.annotations.SIN_ALIAS")
    assert sin["kind"] == "AliasSymbol"
    # raw repr will show it's a function object


def test_class_vars_scanned(idx):
    cv = get(idx, "tests.annotations.ClassVarExample")
    names = [n for (n, _k) in cv["members"]]
    assert "y" in names


def test_td_inheritance(idx):
    sub = get(idx, "tests.annotations.SubTD")
    assert sub["kind"] == "ClassSymbol"
    # td base shows up as a base site
    assert any(b["role"] == "base" for b in sub["bases"])


def test_site_provenance():
    ann = importlib.import_module("tests.annotations")
    mi = scan_module(ann)
    sym = next(s for s in mi.symbols if s.name == "SITE_PROV_VAR")
    assert sym.prov is not None
    assert sym.site.prov is sym.prov

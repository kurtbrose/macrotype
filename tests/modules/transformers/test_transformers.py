from __future__ import annotations

import linecache
import textwrap
import typing as t
from types import ModuleType

import pytest

from macrotype.meta_types import clear_registry
from macrotype.modules.scanner import scan_module
from macrotype.modules.symbols import AliasSymbol, ClassSymbol, FuncSymbol, VarSymbol
from macrotype.modules.transformers import (
    add_comments,
    canonicalize_foreign_symbols,
    expand_overloads,
    normalize_descriptors,
    normalize_flags,
    prune_inherited_typeddict_fields,
    prune_protocol_methods,
    synthesize_aliases,
    transform_dataclasses,
    transform_enums,
)


def mod_from_code(code: str, name: str) -> ModuleType:
    module = ModuleType(name)
    code = textwrap.dedent(code)
    filename = "<" + name + ">"
    linecache.cache[filename] = (len(code), None, code.splitlines(True), filename)
    module.__file__ = filename
    exec(compile(code, filename, "exec"), module.__dict__)
    return module


def test_add_comment_transform() -> None:
    code = """
    x: int = 0  # variable comment

    type Alias = int  # alias comment

    """
    mod = mod_from_code(code, "comments")
    mi = scan_module(mod)
    add_comments(mi)
    by_name = {s.name: s for s in mi.symbols}

    x = by_name["x"]
    assert x.comment == "variable comment"

    alias = by_name["Alias"]
    assert isinstance(alias, AliasSymbol)
    assert alias.comment == "alias comment"
    assert alias.value.comment == "alias comment"


def test_alias_transform() -> None:
    code = """
    from typing import TypeAliasType, TypeVar, TypeAlias

    T = TypeVar("T")
    Alias = TypeAliasType("Alias", list[T], type_params=(T,))
    """
    mod = mod_from_code(code, "alias")
    mi = scan_module(mod)
    synthesize_aliases(mi)
    by_name = {s.name: s for s in mi.symbols}

    alias = t.cast(AliasSymbol, by_name["Alias"])
    assert alias.type_params == ("T",)
    assert t.get_origin(alias.value.annotation) is list


def test_dataclass_transform() -> None:
    code = """
    from dataclasses import dataclass

    @dataclass(order=True)
    class DC:
        x: int
        def user(self) -> None: ...

    @dataclass
    class Outer:
        y: int
        @dataclass
        class Inner:
            z: int
    """
    mod = mod_from_code(code, "dataclasses")
    mi = scan_module(mod)
    transform_dataclasses(mi)
    by_name = {s.name: s for s in mi.symbols}

    dc = t.cast(ClassSymbol, by_name["DC"])
    assert "dataclass(order=True)" in dc.decorators
    member_names = {m.name for m in dc.members}
    assert "__init__" not in member_names
    assert "__lt__" not in member_names

    outer = t.cast(ClassSymbol, by_name["Outer"])
    assert "dataclass" in outer.decorators
    inner = next(m for m in outer.members if isinstance(m, ClassSymbol) and m.name == "Inner")
    assert "dataclass" in inner.decorators


def test_descriptor_transform() -> None:
    code = """
    import functools

    class D:
        @property
        def prop(self) -> int: ...
        @prop.setter
        def prop(self, v: int) -> None: ...
        @prop.deleter
        def prop(self) -> None: ...

        @classmethod
        def clsmeth(cls) -> None: ...

        @staticmethod
        def stat() -> None: ...

        @functools.cached_property
        def cache(self) -> int: ...

        def base(self, a: int, b: str) -> str: ...
        pm = functools.partialmethod(base, 2)
    """
    mod = mod_from_code(code, "descriptor")
    mi = scan_module(mod)
    normalize_descriptors(mi)
    dcls = t.cast(
        ClassSymbol, next(s for s in mi.symbols if isinstance(s, ClassSymbol) and s.name == "D")
    )
    props = [m for m in dcls.members if m.name == "prop" and isinstance(m, FuncSymbol)]
    decos = {tuple(m.decorators) for m in props}
    assert ("property",) in decos
    assert ("prop.setter",) in decos
    assert ("prop.deleter",) in decos
    cm = next(m for m in dcls.members if isinstance(m, FuncSymbol) and m.name == "clsmeth")
    assert cm.decorators == ("classmethod",)
    sm = next(m for m in dcls.members if isinstance(m, FuncSymbol) and m.name == "stat")
    assert sm.decorators == ("staticmethod",)
    cp = next(m for m in dcls.members if isinstance(m, FuncSymbol) and m.name == "cache")
    assert cp.decorators == ("cached_property",)
    pm = next(m for m in dcls.members if isinstance(m, FuncSymbol) and m.name == "pm")
    assert pm.decorators == ()
    assert [p.name for p in pm.params] == ["b"]
    assert pm.params[0].annotation in (str, "str")
    assert pm.ret and pm.ret.annotation in (str, "str")


def test_flag_transform() -> None:
    code = """
    from typing import final, override
    import abc

    @final
    class Base:
        def meth(self) -> None: ...

    class Derived(Base):
        @override
        def meth(self) -> None: ...

    class Abstract(abc.ABC):
        @abc.abstractmethod
        def abst(self) -> None: ...

    @final
    def f() -> None: ...
    """
    mod = mod_from_code(code, "flags")
    mi = scan_module(mod)
    normalize_flags(mi)
    by_name = {s.name: s for s in mi.symbols}

    base = t.cast(ClassSymbol, by_name["Base"])
    assert base.flags.get("final") is True
    assert "final" in base.decorators

    derived = t.cast(ClassSymbol, by_name["Derived"])
    meth = next(m for m in derived.members if isinstance(m, FuncSymbol) and m.name == "meth")
    assert meth.flags.get("override") is True
    assert "override" in meth.decorators

    abstract = t.cast(ClassSymbol, by_name["Abstract"])
    assert abstract.flags.get("abstract") is True
    abst = next(m for m in abstract.members if isinstance(m, FuncSymbol) and m.name == "abst")
    assert abst.flags.get("abstract") is True
    assert "abstractmethod" in abst.decorators

    func = t.cast(FuncSymbol, by_name["f"])
    assert func.flags.get("final") is True
    assert "final" not in func.decorators


def test_foreign_symbol_transform() -> None:
    code = """

    class Dummy:
        __module__ = "other"
        __name__ = "Dummy"

    external = Dummy()
    const = 1
    annotated: int = 2

    def local() -> None: ...
    """
    mod = mod_from_code(code, "foreign")
    mi = scan_module(mod)
    canonicalize_foreign_symbols(mi)
    by_name = {s.name: s for s in mi.symbols}

    external = by_name["external"]
    assert isinstance(external, AliasSymbol)
    const = by_name["const"]
    assert isinstance(const, VarSymbol)
    annotated = by_name["annotated"]
    assert isinstance(annotated, VarSymbol)


def test_overload_transform() -> None:
    clear_registry()
    code = """
    from macrotype.meta_types import overload, overload_for

    @overload
    def foo(x: int) -> int: ...
    @overload
    def foo(x: str) -> str: ...
    def foo(x): ...

    class C:
        @overload
        def bar(self, x: int) -> int: ...
        @overload
        def bar(self, x: str) -> str: ...
        def bar(self, x): ...

    @overload_for(1)
    @overload_for("a")
    def lit(x):
        return x
    """
    mod = mod_from_code(code, "overload")
    mi = scan_module(mod)
    expand_overloads(mi)
    by_name = [s for s in mi.symbols if isinstance(s, FuncSymbol) and s.name == "foo"]
    assert len(by_name) == 2
    assert all("overload" in s.decorators for s in by_name)
    cls = next(s for s in mi.symbols if isinstance(s, ClassSymbol) and s.name == "C")
    bars = [m for m in cls.members if isinstance(m, FuncSymbol) and m.name == "bar"]
    assert len(bars) == 2
    assert all("overload" in m.decorators for m in bars)
    lits = [s for s in mi.symbols if isinstance(s, FuncSymbol) and s.name == "lit"]
    assert len(lits) == 3
    assert all("overload" in s.decorators for s in lits)


def test_protocol_transform() -> None:
    code = """
    from typing import Protocol

    class P(Protocol):
        def meth(self) -> None: ...
    """
    mod = mod_from_code(code, "proto")
    mi = scan_module(mod)
    prune_protocol_methods(mi)
    proto = t.cast(
        ClassSymbol, next(s for s in mi.symbols if isinstance(s, ClassSymbol) and s.name == "P")
    )
    member_names = {m.name for m in proto.members if isinstance(m, FuncSymbol)}
    assert member_names == {"meth"}


@pytest.mark.skip(reason="TypedDict base classes not in MRO at runtime")
def test_typeddict_transform() -> None:
    code = """
    from typing import TypedDict

    class Base(TypedDict):
        a: int
        b: str

    class Derived(Base):
        b: str
        c: float
    """
    mod = mod_from_code(code, "typeddict")
    mi = scan_module(mod)
    prune_inherited_typeddict_fields(mi)
    derived = next(s for s in mi.symbols if isinstance(s, ClassSymbol) and s.name == "Derived")
    assert len(derived.td_fields) == 1
    assert derived.td_fields[0].name == "c"
    assert derived.td_total is None


def test_enum_transform() -> None:
    code = """
    from enum import Enum, IntFlag

    class Color(Enum):
        RED = 1
        GREEN = 2
        def describe(self) -> str: ...

    class Permission(IntFlag):
        READ = 1
        WRITE = 2
    """
    mod = mod_from_code(code, "enums")
    mi = scan_module(mod)
    transform_enums(mi)
    color = t.cast(
        ClassSymbol, next(s for s in mi.symbols if isinstance(s, ClassSymbol) and s.name == "Color")
    )
    aliases = [m for m in color.members if isinstance(m, AliasSymbol)]
    assert [a.name for a in aliases] == ["RED", "GREEN"]
    methods = {m.name for m in color.members if isinstance(m, FuncSymbol)}
    assert "describe" in methods and "__new__" not in methods
    perm = t.cast(
        ClassSymbol,
        next(s for s in mi.symbols if isinstance(s, ClassSymbol) and s.name == "Permission"),
    )
    perm_aliases = [m.name for m in perm.members if isinstance(m, AliasSymbol)]
    assert perm_aliases == ["READ", "WRITE"]
    perm_methods = {m.name for m in perm.members if isinstance(m, FuncSymbol)}
    assert "__or__" not in perm_methods

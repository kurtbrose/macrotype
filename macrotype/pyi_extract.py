from __future__ import annotations
from dataclasses import dataclass, field
import dataclasses
from types import ModuleType
import types
from typing import Any, Callable, get_type_hints, _GenericAlias, get_origin, get_args
import functools
import inspect
import typing
import builtins
import collections.abc


# === Base Class ===

class PyiElement:
    def render(self, indent: int = 0) -> list[str]:
        raise NotImplementedError


# === Helpers ===

@dataclass
class TypeRenderInfo:
    text: str
    used: set[type]

def format_type(tp: Any) -> TypeRenderInfo:
    used: set[type] = set()

    if isinstance(tp, (typing.TypeVar, typing.ParamSpec)):
        used.add(tp)
        return TypeRenderInfo(tp.__name__, used)

    if hasattr(tp, '__supertype__'):
        return TypeRenderInfo(tp.__qualname__, used)

    if tp is type(None):
        return TypeRenderInfo("None", used)
    if tp is Any:
        used.add(Any)
        return TypeRenderInfo("Any", used)

    origin = get_origin(tp)
    args = get_args(tp)

    if origin is Callable or origin is collections.abc.Callable:
        used.add(Callable)
        if args:
            arg_list, ret = args
            if arg_list is Ellipsis:
                ret_fmt = format_type(ret)
                used.update(ret_fmt.used)
                return TypeRenderInfo(f"Callable[..., {ret_fmt.text}]", used)
            if isinstance(arg_list, typing.ParamSpec):
                used.add(arg_list)
                ret_fmt = format_type(ret)
                used.update(ret_fmt.used)
                return TypeRenderInfo(f"Callable[{arg_list.__name__}, {ret_fmt.text}]", used)
            arg_strs = [format_type(a) for a in arg_list]
            used.update(*(a.used for a in arg_strs))
            ret_fmt = format_type(ret)
            used.update(ret_fmt.used)
            arg_str = ", ".join(a.text for a in arg_strs)
            return TypeRenderInfo(f"Callable[[{arg_str}], {ret_fmt.text}]", used)
        return TypeRenderInfo("Callable", used)

    if origin is types.UnionType or origin is typing.Union:
        arg_strs = [format_type(a) for a in args]
        used.update(*(a.used for a in arg_strs))
        text = " | ".join(a.text for a in arg_strs)
        return TypeRenderInfo(text, used)

    if origin is typing.Annotated:
        used.add(typing.Annotated)
        base, *metadata = args
        base_fmt = format_type(base)
        used.update(base_fmt.used)
        metadata_str = ", ".join(repr(m) for m in metadata)
        return TypeRenderInfo(f"Annotated[{base_fmt.text}, {metadata_str}]", used)

    if origin:
        origin_name = getattr(origin, '__qualname__', str(origin))
        used.add(origin)
        if args:
            arg_strs = [format_type(a) for a in args]
            used.update(*(a.used for a in arg_strs))
            args_str = ", ".join(a.text for a in arg_strs)
            return TypeRenderInfo(f"{origin_name}[{args_str}]", used)
        else:
            return TypeRenderInfo(origin_name, used)

    if hasattr(tp, '__args__'):
        arg_strs = [format_type(a) for a in tp.__args__]
        used.update(*(a.used for a in arg_strs))
        args_str = ", ".join(a.text for a in arg_strs)
        return TypeRenderInfo(f"{tp.__class__.__name__}[{args_str}]", used)

    if isinstance(tp, type):
        used.add(tp)
        return TypeRenderInfo(tp.__name__, used)
    if hasattr(tp, '_name') and tp._name:
        return TypeRenderInfo(tp._name, used)

    return TypeRenderInfo(repr(tp), used)


def find_typevars(tp: Any) -> set[str]:
    found = set()
    if isinstance(tp, (typing.TypeVar, typing.ParamSpec)):
        found.add(tp.__name__)
    elif hasattr(tp, '__parameters__'):
        for p in tp.__parameters__:
            found.update(find_typevars(p))
    elif hasattr(tp, '__args__'):
        for a in tp.__args__:
            found.update(find_typevars(a))
    return found


# === Variable ===

@dataclass
class PyiVariable(PyiElement):
    name: str
    type_str: str
    used_types: set[type] = field(default_factory=set)

    def render(self, indent: int = 0) -> list[str]:
        space = "    " * indent
        return [f"{space}{self.name}: {self.type_str}"]

    @classmethod
    def from_assignment(cls, name: str, value: Any) -> PyiVariable:
        return cls(name=name, type_str=type(value).__name__)


# === Alias ===

@dataclass
class PyiAlias(PyiElement):
    name: str
    value: str
    used_types: set[type] = field(default_factory=set)

    def render(self, indent: int = 0) -> list[str]:
        space = "    " * indent
        return [f"{space}{self.name} = {self.value}"]


# === Function ===

@dataclass
class PyiFunction(PyiElement):
    name: str
    args: list[tuple[str, str | None]]
    return_type: str = ""
    decorators: list[str] = field(default_factory=list)
    type_params: list[str] = field(default_factory=list)
    used_types: set[type] = field(default_factory=set)

    def render(self, indent: int = 0) -> list[str]:
        space = "    " * indent
        lines = [f"{space}@{d}" for d in self.decorators]
        parts = []
        for n, t in self.args:
            if t is None:
                parts.append(n)
            else:
                parts.append(f"{n}: {t}")
        args_str = ", ".join(parts)
        tp_str = f"[{', '.join(self.type_params)}]" if self.type_params else ""
        if self.return_type:
            lines.append(f"{space}def {self.name}{tp_str}({args_str}) -> {self.return_type}: ...")
        else:
            lines.append(f"{space}def {self.name}{tp_str}({args_str}): ...")
        return lines

    @classmethod
    def from_function(cls, fn: Callable, decorators: list[str] | None = None) -> PyiFunction:
        try:
            hints = get_type_hints(fn)
        except Exception:
            hints = {}

        sig = inspect.signature(fn)
        args = []
        used_types = set()
        for name, param in sig.parameters.items():
            if param.annotation is inspect._empty:
                if name in {'self', 'cls'}:
                    args.append((name, None))
                else:
                    args.append((name, 'Any'))
                    used_types.add(Any)
                continue
            hint = hints.get(name, 'Any')
            fmt = format_type(hint)
            used_types.update(fmt.used)
            args.append((name, fmt.text))

        if 'return' in hints:
            return_fmt = format_type(hints['return'])
            used_types.update(return_fmt.used)
            ret_text = return_fmt.text
        else:
            ret_text = ""

        all_types = list(hints.values())
        type_params = sorted(find_typevars(tp) for tp in all_types)
        flat_params = sorted(set().union(*type_params))

        decorators = decorators or []
        if "overload" in decorators:
            used_types.add(typing.overload)

        return cls(
            name=fn.__name__,
            args=args,
            return_type=ret_text,
            decorators=decorators,
            type_params=flat_params,
            used_types=used_types,
        )


# === Class ===

@dataclass
class PyiClass(PyiElement):
    name: str
    bases: list[str] = field(default_factory=list)
    body: list[PyiElement] = field(default_factory=list)
    typeddict_total: bool | None = None
    decorators: list[str] = field(default_factory=list)
    used_types: set[type] = field(default_factory=set)

    def render(self, indent: int = 0) -> list[str]:
        space = "    " * indent
        base_decl = ""
        if self.typeddict_total is False:
            base_decl = "(TypedDict, total=False)"
        elif self.typeddict_total is True:
            base_decl = "(TypedDict)"
        elif self.bases:
            base_decl = f"({', '.join(self.bases)})"
        lines = [f"{space}@{d}" for d in self.decorators]
        lines.append(f"{space}class {self.name}{base_decl}:")
        if self.body:
            for item in self.body:
                lines.extend(item.render(indent + 1))
        else:
            lines.append(f"{space}    pass")
        return lines

    @classmethod
    def from_class(cls, klass: type) -> "PyiClass":
        is_typeddict = isinstance(klass, typing._TypedDictMeta)
        members: list[PyiElement] = []
        typeddict_total = klass.__dict__.get("__total__", True) if is_typeddict else None
        decorators: list[str] = []
        used_types: set[type] = set()

        if is_typeddict:
            bases = ["TypedDict"]
        else:
            raw_bases = getattr(klass, "__orig_bases__", None) or klass.__bases__
            bases = []
            for b in raw_bases:
                if b is object:
                    continue
                fmt = format_type(b)
                bases.append(fmt.text)
                used_types.update(fmt.used)

        is_dataclass_obj = dataclasses.is_dataclass(klass) or hasattr(klass, "__dataclass_fields__")
        if is_dataclass_obj:
            params = getattr(klass, "__dataclass_params__", None)
            args: list[str] = []
            if params is not None:
                defaults = {
                    "init": True,
                    "repr": True,
                    "eq": True,
                    "order": False,
                    "unsafe_hash": False,
                    "frozen": False,
                    "match_args": True,
                    "kw_only": False,
                    "slots": False,
                    "weakref_slot": False,
                }
                for name, default in defaults.items():
                    val = getattr(params, name, default)
                    if val != default:
                        args.append(f"{name}={val}")
            deco = "dataclass" + (f"({', '.join(args)})" if args else "")
            decorators.append(deco)
            used_types.add(dataclasses.dataclass)

        raw_ann = klass.__dict__.get("__annotations__", {})
        try:
            globalns = vars(inspect.getmodule(klass))
            resolved = {
                name: get_type_hints(klass, globalns=globalns, localns=klass.__dict__).get(name, tp)
                for name, tp in raw_ann.items()
            }
        except Exception:
            resolved = raw_ann

        for name, tp in resolved.items():
            fmt = format_type(tp)
            members.append(PyiVariable(name, fmt.text, fmt.used))

        if not is_typeddict:
            auto_methods = {
                "__init__",
                "__repr__",
                "__eq__",
                "__lt__",
                "__le__",
                "__gt__",
                "__ge__",
                "__hash__",
                "__setattr__",
                "__delattr__",
                "__getstate__",
                "__setstate__",
                "_dataclass_getstate",
                "_dataclass_setstate",
                "__getattribute__",
            } if is_dataclass_obj else set()

            for attr_name, attr in klass.__dict__.items():
                if attr_name in auto_methods:
                    continue
                if inspect.isfunction(attr):
                    ovs = typing.get_overloads(attr)
                    if ovs:
                        for ov in ovs:
                            members.append(PyiFunction.from_function(ov, decorators=["overload"]))
                    members.append(PyiFunction.from_function(attr))
                elif isinstance(attr, classmethod):
                    members.append(PyiFunction.from_function(attr.__func__, decorators=["classmethod"]))
                elif isinstance(attr, staticmethod):
                    members.append(PyiFunction.from_function(attr.__func__, decorators=["staticmethod"]))
                elif isinstance(attr, property):
                    members.append(PyiFunction.from_function(attr.fget, decorators=["property"]))
                elif isinstance(attr, functools.cached_property):
                    members.append(PyiFunction.from_function(attr.func, decorators=["cached_property"]))
                    used_types.add(functools.cached_property)
                elif inspect.isclass(attr):
                    if attr.__qualname__.startswith(klass.__qualname__ + "."):
                        members.append(PyiClass.from_class(attr))

        return cls(
            name=klass.__name__,
            bases=bases,
            body=members,
            typeddict_total=typeddict_total,
            decorators=decorators,
            used_types=used_types,
        )


# === Module ===

@dataclass
class PyiModule:
    imports: list[str] = field(default_factory=list)
    body: list[PyiElement] = field(default_factory=list)

    def render(self, indent: int = 0) -> list[str]:
        lines = list(self.imports)
        if lines:
            lines.append("")
        for item in self.body:
            lines.extend(item.render(indent))
            lines.append("")
        return lines[:-1] if lines and lines[-1] == "" else lines

    @classmethod
    def from_module(cls, mod: ModuleType) -> PyiModule:
        seen: dict[int, str] = {}
        body: list[PyiElement] = []
        used_types: set[type] = set()
        mod_name = mod.__name__
        globals_dict = vars(mod)

        for name, obj in globals_dict.items():
            if not hasattr(obj, '__module__') or obj.__module__ != mod_name:
                continue
            if id(obj) in seen:
                continue
            seen[id(obj)] = name

            if inspect.isfunction(obj):
                ovs = typing.get_overloads(obj)
                if ovs:
                    for ov in ovs:
                        ofunc = PyiFunction.from_function(ov, decorators=["overload"])
                        used_types.update(ofunc.used_types)
                        body.append(ofunc)
                func = PyiFunction.from_function(obj)
                used_types.update(func.used_types)
                body.append(func)
            elif inspect.isclass(obj):
                cls_obj = PyiClass.from_class(obj)
                used_types.update(cls_obj.used_types)
                for item in cls_obj.body:
                    if isinstance(item, (PyiFunction, PyiVariable)):
                        used_types.update(getattr(item, 'used_types', set()))
                body.append(cls_obj)
            elif callable(obj) and hasattr(obj, '__supertype__'):
                base_fmt = format_type(obj.__supertype__)
                alias_used = {typing.NewType, *base_fmt.used}
                used_types.update(alias_used)
                body.append(PyiAlias(name=name, value=f"NewType('{name}', {base_fmt.text})", used_types=alias_used))
            elif isinstance(obj, (int, str, float, bool)):
                body.append(PyiVariable.from_assignment(name, obj))

        typing_names = sorted(
            t.__name__ for t in used_types
            if getattr(t, '__module__', '') == 'typing'
            and not isinstance(t, (typing.TypeVar, typing.ParamSpec))
        )

        external_imports = {}
        for t in used_types:
            modname = getattr(t, '__module__', None)
            name = getattr(t, '__name__', None)
            if not modname or not name:
                continue
            if modname in ("builtins", "typing", mod_name):
                continue
            external_imports.setdefault(modname, set()).add(name)

        import_lines = []
        if typing_names:
            import_lines.append(f"from typing import {', '.join(typing_names)}")
        for modname, names in sorted(external_imports.items()):
            import_lines.append(f"from {modname} import {', '.join(sorted(names))}")

        return cls(imports=import_lines, body=body)


# === Demo Smoke Test ===

def _demo():
    mod = PyiModule.from_module(inspect.getmodule(_demo))
    for line in mod.render():
        print(line)




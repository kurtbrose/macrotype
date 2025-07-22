from __future__ import annotations
from dataclasses import dataclass, field
import dataclasses
from types import ModuleType
import types
from typing import Any, Callable, get_type_hints, get_origin, get_args
import functools
import inspect
import typing

_INDENT = "    "

try:
    from typing import get_overloads as _get_overloads
except ImportError:  # pragma: no cover - Python < 3.11
    try:
        from typing_extensions import get_overloads as _get_overloads
    except Exception:  # pragma: no cover - very old typing
        def _get_overloads(func):
            return []
import collections.abc


# === Base Class ===

class PyiElement:
    """Abstract representation of an element in a ``.pyi`` file."""

    def render(self, indent: int = 0) -> list[str]:
        """Return the lines for this element indented by ``indent`` levels."""
        raise NotImplementedError

    @staticmethod
    def _space(indent: int) -> str:
        return _INDENT * indent


@dataclass
class PyiNamedElement(PyiElement):
    """Base class for named elements that track used types."""

    name: str
    used_types: set[type] = field(default_factory=set, kw_only=True)


# === Helpers ===

@dataclass
class TypeRenderInfo:
    """Formatted representation of a type along with the used types."""

    text: str
    used: set[type]

def format_type(tp: Any) -> TypeRenderInfo:
    """Return a ``TypeRenderInfo`` instance for ``tp``."""

    used: set[type] = set()

    if isinstance(tp, (typing.TypeVar, typing.ParamSpec, typing.TypeVarTuple)):
        used.add(tp)
        return TypeRenderInfo(tp.__name__, used)

    if hasattr(tp, '__supertype__'):
        return TypeRenderInfo(tp.__qualname__, used)

    if tp is type(None):
        return TypeRenderInfo("None", used)
    if tp is typing.Self:
        used.add(typing.Self)
        return TypeRenderInfo("Self", used)
    if tp is Any:
        used.add(Any)
        return TypeRenderInfo("Any", used)

    origin = get_origin(tp)
    args = get_args(tp)

    if origin in {Callable, collections.abc.Callable}:
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

    if origin in {types.UnionType, typing.Union}:
        arg_strs = [format_type(a) for a in args]
        used.update(*(a.used for a in arg_strs))
        text = " | ".join(a.text for a in arg_strs)
        return TypeRenderInfo(text, used)

    if origin is typing.Unpack:
        used.add(typing.Unpack)
        if args:
            arg_fmt = format_type(args[0])
            used.update(arg_fmt.used)
            return TypeRenderInfo(f"Unpack[{arg_fmt.text}]", used)
        return TypeRenderInfo("Unpack", used)

    if origin is typing.Annotated:
        used.add(typing.Annotated)
        base, *metadata = args
        base_fmt = format_type(base)
        used.update(base_fmt.used)
        metadata_str = ", ".join(repr(m) for m in metadata)
        return TypeRenderInfo(f"Annotated[{base_fmt.text}, {metadata_str}]", used)

    if origin is tuple and len(args) == 2 and args[1] is Ellipsis:
        used.add(tuple)
        arg_fmt = format_type(args[0])
        used.update(arg_fmt.used)
        return TypeRenderInfo(f"tuple[{arg_fmt.text}, ...]", used)

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
    """Return a set of type variable names referenced by ``tp``."""

    found = set()
    if isinstance(tp, typing.TypeVar):
        found.add(tp.__name__)
    elif isinstance(tp, typing.ParamSpec):
        found.add(f"**{tp.__name__}")
    elif isinstance(tp, typing.TypeVarTuple):
        found.add(f"*{tp.__name__}")
    elif hasattr(tp, '__parameters__'):
        for p in tp.__parameters__:
            found.update(find_typevars(p))
    elif hasattr(tp, '__args__'):
        for a in tp.__args__:
            found.update(find_typevars(a))
    return found


# Defaults used when recreating a ``@dataclass`` decorator.
_DATACLASS_DEFAULTS: dict[str, Any] = {
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

# Methods automatically generated by ``dataclasses`` which should not appear in
# generated stubs.
_AUTO_DATACLASS_METHODS = {
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
    "__replace__",
}


def _dataclass_decorator(klass: type) -> tuple[str, set[type]] | None:
    """Return the ``@dataclass`` decorator text for *klass*."""

    if not (
        dataclasses.is_dataclass(klass)
        or hasattr(klass, "__dataclass_fields__")
    ):
        return None

    params = getattr(klass, "__dataclass_params__", None)
    args: list[str] = []
    if params is not None:
        for name, default in _DATACLASS_DEFAULTS.items():
            if name == "match_args" and not hasattr(params, "match_args"):
                continue
            val = getattr(params, name, default)
            if name == "slots" and not hasattr(params, name):
                val = not hasattr(klass, "__dict__")
            elif name == "weakref_slot" and not hasattr(params, name):
                val = "__weakref__" in getattr(klass, "__slots__", ())
            if val != default:
                args.append(f"{name}={val}")

    deco = "dataclass" + (f"({', '.join(args)})" if args else "")
    return deco, {dataclasses.dataclass}


# === Variable ===

@dataclass
class PyiVariable(PyiNamedElement):
    type_str: str

    def render(self, indent: int = 0) -> list[str]:
        space = self._space(indent)
        return [f"{space}{self.name}: {self.type_str}"]

    @classmethod
    def from_assignment(cls, name: str, value: Any) -> PyiVariable:
        """Create a :class:`PyiVariable` from an assignment value."""

        return cls(name=name, type_str=type(value).__name__)


# === Alias ===

@dataclass
class PyiAlias(PyiNamedElement):
    value: str

    def render(self, indent: int = 0) -> list[str]:
        """Return the pyi representation for this alias."""

        space = self._space(indent)
        return [f"{space}{self.name} = {self.value}"]


# === Function ===

@dataclass
class PyiFunction(PyiNamedElement):
    args: list[tuple[str, str | None]]
    return_type: str = ""
    decorators: list[str] = field(default_factory=list)
    type_params: list[str] = field(default_factory=list)

    def render(self, indent: int = 0) -> list[str]:
        space = self._space(indent)
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
    def from_function(
        cls,
        fn: Callable,
        decorators: list[str] | None = None,
        exclude_params: set[str] | None = None,
    ) -> PyiFunction:
        """Create a :class:`PyiFunction` from ``fn``."""

        try:
            hints = get_type_hints(fn)
        except Exception:
            hints = {}

        sig = inspect.signature(fn)
        args = []
        used_types = set()
        for name, param in sig.parameters.items():
            display_name = name
            if param.kind is inspect.Parameter.VAR_POSITIONAL:
                display_name = f"*{name}"
            elif param.kind is inspect.Parameter.VAR_KEYWORD:
                display_name = f"**{name}"

            if param.annotation is inspect._empty:
                if name in {'self', 'cls'}:
                    args.append((display_name, None))
                else:
                    args.append((display_name, 'Any'))
                    used_types.add(Any)
                continue
            hint = hints.get(name, 'Any')
            fmt = format_type(hint)
            used_types.update(fmt.used)
            args.append((display_name, fmt.text))

        if 'return' in hints:
            return_fmt = format_type(hints['return'])
            used_types.update(return_fmt.used)
            ret_text = return_fmt.text
        else:
            ret_text = ""

        all_types = list(hints.values())
        type_params = sorted(find_typevars(tp) for tp in all_types)
        flat_params = sorted(set().union(*type_params)) if type_params else []
        if exclude_params:
            flat_params = [p for p in flat_params if p.lstrip('*') not in exclude_params]

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
class PyiClass(PyiNamedElement):
    bases: list[str] = field(default_factory=list)
    type_params: list[str] = field(default_factory=list)
    body: list[PyiElement] = field(default_factory=list)
    typeddict_total: bool | None = None
    decorators: list[str] = field(default_factory=list)

    def render(self, indent: int = 0) -> list[str]:
        space = self._space(indent)
        base_decl = ""
        if self.typeddict_total is False:
            base_decl = "(TypedDict, total=False)"
        elif self.typeddict_total is True:
            base_decl = "(TypedDict)"
        elif self.bases:
            base_decl = f"({', '.join(self.bases)})"

        tp_str = f"[{', '.join(self.type_params)}]" if self.type_params else ""

        lines = [f"{space}@{d}" for d in self.decorators]
        lines.append(f"{space}class {self.name}{tp_str}{base_decl}:")
        if self.body:
            for item in self.body:
                lines.extend(item.render(indent + 1))
        else:
            lines.append(f"{space}    pass")
        return lines

    @classmethod
    def from_class(cls, klass: type) -> "PyiClass":
        """Create a :class:`PyiClass` representation of ``klass``."""

        is_typeddict = isinstance(klass, typing._TypedDictMeta)
        members: list[PyiElement] = []
        typeddict_total = klass.__dict__.get("__total__", True) if is_typeddict else None
        decorators: list[str] = []
        used_types: set[type] = set()
        class_params: set[str] = {t.__name__ for t in getattr(klass, '__parameters__', ())}

        type_params: list[str] = []
        if is_typeddict:
            bases = ["TypedDict"]
            used_types.add(typing.TypedDict)
        else:
            raw_bases = getattr(klass, "__orig_bases__", None) or klass.__bases__
            bases = []
            for b in raw_bases:
                if b is object:
                    continue
                if get_origin(b) is typing.Generic:
                    for param in get_args(b):
                        fmt = format_type(param)
                        type_params.append(fmt.text)
                        used_types.update(fmt.used)
                    continue
                fmt = format_type(b)
                bases.append(fmt.text)
                used_types.update(fmt.used)

        deco_info = _dataclass_decorator(klass)
        is_dataclass_obj = deco_info is not None
        if deco_info:
            deco, used = deco_info
            decorators.append(deco)
            used_types.update(used)

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
            members.append(
                PyiVariable(name=name, type_str=fmt.text, used_types=fmt.used)
            )

        if not is_typeddict:
            auto_methods = _AUTO_DATACLASS_METHODS if is_dataclass_obj else set()

            for attr_name, attr in klass.__dict__.items():
                if attr_name in auto_methods:
                    continue
                if inspect.isfunction(attr):
                    ovs = _get_overloads(attr)
                    if ovs:
                        for ov in ovs:
                            members.append(
                                PyiFunction.from_function(ov, decorators=["overload"], exclude_params=class_params)
                            )
                    members.append(PyiFunction.from_function(attr, exclude_params=class_params))
                elif isinstance(attr, classmethod):
                    members.append(
                        PyiFunction.from_function(
                            attr.__func__, decorators=["classmethod"], exclude_params=class_params
                        )
                    )
                elif isinstance(attr, staticmethod):
                    members.append(
                        PyiFunction.from_function(
                            attr.__func__, decorators=["staticmethod"], exclude_params=class_params
                        )
                    )
                elif isinstance(attr, property):
                    members.append(
                        PyiFunction.from_function(
                            attr.fget, decorators=["property"], exclude_params=class_params
                        )
                    )
                elif isinstance(attr, functools.cached_property):
                    members.append(
                        PyiFunction.from_function(
                            attr.func, decorators=["cached_property"], exclude_params=class_params
                        )
                    )
                    used_types.add(functools.cached_property)
                elif inspect.isclass(attr):
                    if attr.__qualname__.startswith(klass.__qualname__ + "."):
                        members.append(PyiClass.from_class(attr))

        return cls(
            name=klass.__name__,
            bases=bases,
            type_params=type_params,
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
        """Create a :class:`PyiModule` from a live module object."""

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
                ovs = _get_overloads(obj)
                if ovs:
                    for ov in ovs:
                        ofunc = PyiFunction.from_function(ov, decorators=["overload"])
                        used_types.update(ofunc.used_types)
                        body.append(ofunc)
                else:
                    func = PyiFunction.from_function(obj)
                    used_types.update(func.used_types)
                    body.append(func)
            elif inspect.isclass(obj):
                cls_obj = PyiClass.from_class(obj)
                if cls_obj.name != name:
                    cls_obj.name = name
                used_types.update(cls_obj.used_types)
                for item in cls_obj.body:
                    if isinstance(item, (PyiFunction, PyiVariable)):
                        used_types.update(getattr(item, 'used_types', set()))
                body.append(cls_obj)
            elif callable(obj) and hasattr(obj, '__supertype__'):
                base_fmt = format_type(obj.__supertype__)
                alias_used = {typing.NewType, *base_fmt.used}
                used_types.update(alias_used)
                body.append(
                    PyiAlias(
                        name=name,
                        value=f"NewType('{name}', {base_fmt.text})",
                        used_types=alias_used,
                    )
                )
            elif isinstance(obj, typing.TypeVarTuple):
                alias_used = {typing.TypeVarTuple}
                used_types.update(alias_used)
                body.append(
                    PyiAlias(
                        name=name,
                        value=f"TypeVarTuple('{obj.__name__}')",
                        used_types=alias_used,
                    )
                )
            elif isinstance(obj, typing.TypeVar):
                alias_used = {typing.TypeVar}
                used_types.update(alias_used)
                body.append(
                    PyiAlias(
                        name=name,
                        value=f"TypeVar('{obj.__name__}')",
                        used_types=alias_used,
                    )
                )
            elif isinstance(obj, typing.ParamSpec):
                alias_used = {typing.ParamSpec}
                used_types.update(alias_used)
                body.append(
                    PyiAlias(
                        name=name,
                        value=f"ParamSpec('{obj.__name__}')",
                        used_types=alias_used,
                    )
                )
            elif isinstance(obj, (int, str, float, bool)):
                body.append(PyiVariable.from_assignment(name, obj))

        typing_names = sorted(
            t.__name__
            for t in used_types
            if getattr(t, '__module__', '') == 'typing'
            and not isinstance(t, (typing.TypeVar, typing.ParamSpec, typing.TypeVarTuple))
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




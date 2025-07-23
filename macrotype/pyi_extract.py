from __future__ import annotations

"""Utilities for building ``.pyi`` objects from live Python modules."""

from dataclasses import dataclass, field
import dataclasses
import enum
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
import collections
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

def format_type(type_obj: Any) -> TypeRenderInfo:
    """Return a ``TypeRenderInfo`` instance for ``type_obj``."""

    used: set[type] = set()

    if isinstance(type_obj, (typing.TypeVar, typing.ParamSpec, typing.TypeVarTuple)):
        used.add(type_obj)
        return TypeRenderInfo(type_obj.__name__, used)

    if hasattr(type_obj, "__supertype__"):
        return TypeRenderInfo(type_obj.__qualname__, used)

    if type_obj is type(None):
        return TypeRenderInfo("None", used)
    if type_obj is typing.Self:
        used.add(typing.Self)
        return TypeRenderInfo("Self", used)
    if getattr(typing, "Never", None) is not None and type_obj is typing.Never:
        used.add(typing.Never)
        return TypeRenderInfo("Never", used)
    if type_obj is typing.NoReturn:
        used.add(typing.NoReturn)
        return TypeRenderInfo("NoReturn", used)
    if (
        getattr(typing, "LiteralString", None) is not None
        and type_obj is typing.LiteralString
    ):
        used.add(typing.LiteralString)
        return TypeRenderInfo("LiteralString", used)
    if type_obj is Any:
        used.add(Any)
        return TypeRenderInfo("Any", used)

    origin = get_origin(type_obj)
    args = get_args(type_obj)

    if origin is typing.Concatenate:
        used.add(typing.Concatenate)
        arg_parts = [format_type(a) for a in args]
        used.update(*(p.used for p in arg_parts))
        return TypeRenderInfo(
            f"Concatenate[{', '.join(p.text for p in arg_parts)}]",
            used,
        )

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
            if get_origin(arg_list) is typing.Concatenate:
                concat_fmt = format_type(arg_list)
                used.update(concat_fmt.used)
                ret_fmt = format_type(ret)
                used.update(ret_fmt.used)
                return TypeRenderInfo(
                    f"Callable[{concat_fmt.text}, {ret_fmt.text}]",
                    used,
                )
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

    if hasattr(type_obj, "__args__"):
        arg_strs = [format_type(a) for a in type_obj.__args__]
        used.update(*(a.used for a in arg_strs))
        args_str = ", ".join(a.text for a in arg_strs)
        return TypeRenderInfo(f"{type_obj.__class__.__name__}[{args_str}]", used)

    if isinstance(type_obj, type):
        used.add(type_obj)
        return TypeRenderInfo(type_obj.__name__, used)
    if hasattr(type_obj, "_name") and type_obj._name:
        return TypeRenderInfo(type_obj._name, used)

    return TypeRenderInfo(repr(type_obj), used)


def format_type_param(tp: Any) -> TypeRenderInfo:
    """Return formatted text for a type parameter object."""

    prefix = ""
    if isinstance(tp, typing.TypeVarTuple):
        prefix = "*"
    elif isinstance(tp, typing.ParamSpec):
        prefix = "**"

    text = prefix + tp.__name__
    used: set[type] = {tp}

    bound = getattr(tp, "__bound__", None)
    if bound is type(None):
        bound = None
    constraints = getattr(tp, "__constraints__", ()) or ()

    if bound is not None:
        fmt = format_type(bound)
        used.update(fmt.used)
        text += f": {fmt.text}"
    elif constraints:
        parts = [format_type(c) for c in constraints]
        used.update(*(p.used for p in parts))
        text += f": ({', '.join(p.text for p in parts)})"

    if hasattr(tp, "__default__"):
        default = getattr(tp, "__default__")
        if default is not None and default is not typing.NoDefault:
            if isinstance(default, tuple) and all(isinstance(d, type) for d in default):
                parts = [format_type(d) for d in default]
                used.update(*(p.used for p in parts))
                default_str = f"({', '.join(p.text for p in parts)})"
            else:
                fmt = format_type(default)
                used.update(fmt.used)
                default_str = fmt.text
            text += f" = {default_str}"

    return TypeRenderInfo(text, used)


def find_typevars(type_obj: Any) -> set[str]:
    """Return a set of type variable names referenced by ``type_obj``."""

    found = set()
    if isinstance(type_obj, typing.TypeVar):
        found.add(type_obj.__name__)
    elif isinstance(type_obj, typing.ParamSpec):
        found.add(f"**{type_obj.__name__}")
    elif isinstance(type_obj, typing.TypeVarTuple):
        found.add(f"*{type_obj.__name__}")
    elif hasattr(type_obj, "__parameters__"):
        for param in type_obj.__parameters__:
            found.update(find_typevars(param))
    elif hasattr(type_obj, "__args__"):
        for arg in type_obj.__args__:
            found.update(find_typevars(arg))
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


def _dataclass_auto_methods(params: dataclasses._DataclassParams | None) -> set[str]:
    """Return the dataclass-generated methods based on *params*."""

    if params is None:
        return set(_AUTO_DATACLASS_METHODS)

    auto_methods = {
        "__init__",
        "__repr__",
        "__getstate__",
        "__setstate__",
        "_dataclass_getstate",
        "_dataclass_setstate",
        "__getattribute__",
        "__replace__",
    }
    if params.eq:
        auto_methods.add("__eq__")
    if params.order:
        auto_methods.update({"__lt__", "__le__", "__gt__", "__ge__"})
    if params.frozen:
        auto_methods.update({"__setattr__", "__delattr__"})
    if params.eq and (params.frozen or params.unsafe_hash):
        auto_methods.add("__hash__")
    return auto_methods

# Mapping of attribute types to the underlying function attribute and the
# decorator name used when generating stubs for class attributes.
_ATTR_DECORATORS: dict[type, tuple[str, str]] = {
    classmethod: ("__func__", "classmethod"),
    staticmethod: ("__func__", "staticmethod"),
    property: ("fget", "property"),
    functools.cached_property: ("func", "cached_property"),
}

# Mapping of typing alias types to the factory function used to recreate them.
# Types that represent aliases and the factory function used to recreate them
_ALIAS_TYPES: tuple[type, ...] = (
    typing.TypeVarTuple,
    typing.TypeVar,
    typing.ParamSpec,
)


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
        if value is None:
            type_name = "None"
        else:
            type_name = type(value).__name__
        return cls(name=name, type_str=type_name)


# === Alias ===

@dataclass
class PyiAlias(PyiNamedElement):
    value: str
    keyword: str = ""
    type_params: list[str] = field(default_factory=list)

    def render(self, indent: int = 0) -> list[str]:
        """Return the pyi representation for this alias."""

        space = self._space(indent)
        kw = f"{self.keyword} " if self.keyword else ""
        param_str = (
            f"[{', '.join(self.type_params)}]" if self.type_params else ""
        )
        return [f"{space}{kw}{self.name}{param_str} = {self.value}"]


# === Function ===

@dataclass
class PyiFunction(PyiNamedElement):
    args: list[tuple[str, str | None]]
    return_type: str = ""
    decorators: list[str] = field(default_factory=list)
    type_params: list[str] = field(default_factory=list)
    is_async: bool = False

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
        param_str = f"[{', '.join(self.type_params)}]" if self.type_params else ""
        prefix = "async " if self.is_async else ""
        if self.return_type:
            signature = (
                f"{space}{prefix}def {self.name}{param_str}({args_str}) -> {self.return_type}: ..."
            )
        else:
            signature = f"{space}{prefix}def {self.name}{param_str}({args_str}): ..."
        lines.append(signature)
        return lines

    @classmethod
    def from_function(
        cls,
        fn: Callable,
        decorators: list[str] | None = None,
        exclude_params: set[str] | None = None,
        *,
        globalns: dict[str, Any] | None = None,
        localns: dict[str, Any] | None = None,
    ) -> PyiFunction:
        """Create a :class:`PyiFunction` from ``fn``."""

        try:
            hints = get_type_hints(
                fn, globalns=globalns, localns=localns, include_extras=True
            )
        except Exception:
            hints = {}

        sig = inspect.signature(fn)
        args = []
        used_types = set()
        posonly: list[tuple[str, str | None]] = []
        star_added = False

        for name, param in sig.parameters.items():
            display_name = name
            if param.kind is inspect.Parameter.POSITIONAL_ONLY:
                kind = "posonly"
            elif param.kind is inspect.Parameter.VAR_POSITIONAL:
                display_name = f"*{name}"
                star_added = True
                kind = "varpos"
            elif param.kind is inspect.Parameter.KEYWORD_ONLY:
                kind = "kwonly"
            elif param.kind is inspect.Parameter.VAR_KEYWORD:
                display_name = f"**{name}"
                kind = "varkw"
            else:
                kind = "normal"

            if param.annotation is inspect._empty:
                if name in {'self', 'cls'}:
                    ann = None
                else:
                    ann = 'Any'
                    used_types.add(Any)
            else:
                hint = hints.get(name, 'Any')
                fmt = format_type(hint)
                used_types.update(fmt.used)
                ann = fmt.text

            pair = (display_name, ann)

            if kind == "posonly":
                posonly.append(pair)
                continue

            if posonly:
                args.extend(posonly)
                args.append(("/", None))
                posonly.clear()

            if kind == "kwonly" and not star_added:
                args.append(("*", None))
                star_added = True

            args.append(pair)

        if posonly:
            args.extend(posonly)
            args.append(("/", None))

        if 'return' in hints:
            return_fmt = format_type(hints['return'])
            used_types.update(return_fmt.used)
            ret_text = return_fmt.text
        else:
            ret_text = ""

        tp_strings: list[str] = []
        type_param_objs = getattr(fn, "__type_params__", None)
        if type_param_objs:
            for tp in type_param_objs:
                name = tp.__name__
                if exclude_params and name in exclude_params:
                    continue
                fmt = format_type_param(tp)
                tp_strings.append(fmt.text)
                used_types.update(fmt.used)
        else:
            all_types = list(hints.values())
            type_params = sorted(find_typevars(t) for t in all_types)
            flat_params = sorted(set().union(*type_params)) if type_params else []
            if exclude_params:
                flat_params = [p for p in flat_params if p.lstrip('*') not in exclude_params]
            tp_strings = flat_params

        decorators = list(decorators or [])
        if getattr(fn, "__final__", False):
            decorators.append("final")
            used_types.add(typing.final)
        if "overload" in decorators:
            used_types.add(typing.overload)

        is_async = inspect.iscoroutinefunction(fn) or inspect.isasyncgenfunction(fn)

        return cls(
            name=fn.__name__,
            args=args,
            return_type=ret_text,
            decorators=decorators,
            type_params=tp_strings,
            used_types=used_types,
            is_async=is_async,
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

        param_str = f"[{', '.join(self.type_params)}]" if self.type_params else ""

        lines = [f"{space}@{d}" for d in self.decorators]
        lines.append(f"{space}class {self.name}{param_str}{base_decl}:")
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
        is_enum = isinstance(klass, enum.EnumMeta)
        is_namedtuple = issubclass(klass, tuple) and hasattr(klass, "_fields")
        members: list[PyiElement] = []
        typeddict_total = klass.__dict__.get("__total__", True) if is_typeddict else None
        decorators: list[str] = []
        used_types: set[type] = set()
        if getattr(klass, "__final__", False):
            decorators.append("final")
            used_types.add(typing.final)
        if getattr(klass, "_is_runtime_protocol", False):
            decorators.append("runtime_checkable")
            used_types.add(typing.runtime_checkable)
        class_params: set[str] = {t.__name__ for t in getattr(klass, '__parameters__', ())}

        type_params: list[str] = []
        if hasattr(klass, "__type_params__") and klass.__type_params__:
            for tp in klass.__type_params__:
                fmt = format_type_param(tp)
                type_params.append(fmt.text)
                used_types.update(fmt.used)
        elif is_namedtuple:
            bases = ["NamedTuple"]
            used_types.add(typing.NamedTuple)
            raw_bases = getattr(klass, "__orig_bases__", ())
            for b in raw_bases:
                if get_origin(b) is typing.Generic:
                    if not type_params:
                        for param in get_args(b):
                            fmt = format_type(param)
                            type_params.append(fmt.text)
                            used_types.update(fmt.used)
                    continue
            raw_ann = klass.__dict__.get("__annotations__", {})
            for name, annotation in raw_ann.items():
                fmt = format_type(annotation)
                members.append(
                    PyiVariable(name=name, type_str=fmt.text, used_types=fmt.used)
                )
            return cls(
                name=klass.__name__,
                bases=bases,
                type_params=type_params,
                body=members,
                typeddict_total=None,
                decorators=decorators,
                used_types=used_types,
            )
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
                    if not type_params:
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
        if is_typeddict:
            resolved = raw_ann
        else:
            try:
                globalns = vars(inspect.getmodule(klass))
                resolved = {
                    name: get_type_hints(
                        klass,
                        globalns=globalns,
                        localns=klass.__dict__,
                        include_extras=True,
                    ).get(name, annotation)
                    for name, annotation in raw_ann.items()
                }
            except Exception:
                resolved = raw_ann

        for name, annotation in resolved.items():
            fmt = format_type(annotation)
            members.append(
                PyiVariable(name=name, type_str=fmt.text, used_types=fmt.used)
            )

        if is_enum:
            for member_name, member in klass.__members__.items():
                members.append(
                    PyiAlias(
                        name=member_name,
                        value=repr(member.value),
                    )
                )

        if not is_typeddict:
            if is_dataclass_obj:
                params = getattr(klass, "__dataclass_params__", None)
                auto_methods = _dataclass_auto_methods(params)
            else:
                auto_methods = set()
            if is_enum:
                auto_methods.update({"_generate_next_value_", "__new__"})

            protocol_skip: set[str] = set()
            protocol_method_names = {"_proto_hook", "_no_init_or_replace_init"}
            if getattr(klass, "_is_protocol", False):
                protocol_skip.update({"__init__", "__subclasshook__"})

            for attr_name, attr in klass.__dict__.items():
                if attr_name in auto_methods:
                    continue
                if attr_name in protocol_skip or getattr(attr, "__name__", None) in protocol_method_names:
                    continue
                # unwrap decorators that preserve __wrapped__ (e.g. lru_cache)
                # so we treat the original function as a method
                fn_attr = None
                if inspect.isfunction(attr):
                    fn_attr = attr
                elif (
                    callable(attr)
                    and hasattr(attr, "__wrapped__")
                    and inspect.isfunction(attr.__wrapped__)
                    and not isinstance(
                        attr,
                        (
                            classmethod,
                            staticmethod,
                            property,
                            functools.cached_property,
                        ),
                    )
                ):
                    fn_attr = attr.__wrapped__

                if fn_attr is not None:
                    if fn_attr.__name__ == "<lambda>":
                        continue
                    ovs = _get_overloads(fn_attr)
                    if ovs:
                        for ov in ovs:
                            members.append(
                                PyiFunction.from_function(
                                    ov,
                                    decorators=["overload"],
                                    exclude_params=class_params,
                                    globalns=globalns,
                                    localns=klass.__dict__,
                                )
                            )
                    members.append(
                        PyiFunction.from_function(
                            fn_attr,
                            exclude_params=class_params,
                            globalns=globalns,
                            localns=klass.__dict__,
                        )
                    )
                    continue

                handled = False
                for attr_type, (func_attr, deco) in _ATTR_DECORATORS.items():
                    if isinstance(attr, attr_type):
                        func = PyiFunction.from_function(
                            getattr(attr, func_attr),
                            decorators=[deco],
                            exclude_params=class_params,
                            globalns=globalns,
                            localns=klass.__dict__,
                        )
                        members.append(func)
                        used_types.update(func.used_types)
                        if attr_type is property:
                            if attr.fset is not None:
                                setter = PyiFunction.from_function(
                                    attr.fset,
                                    decorators=[f"{attr_name}.setter"],
                                    exclude_params=class_params,
                                    globalns=globalns,
                                    localns=klass.__dict__,
                                )
                                members.append(setter)
                                used_types.update(setter.used_types)
                            if attr.fdel is not None:
                                deleter = PyiFunction.from_function(
                                    attr.fdel,
                                    decorators=[f"{attr_name}.deleter"],
                                    exclude_params=class_params,
                                    globalns=globalns,
                                    localns=klass.__dict__,
                                )
                                members.append(deleter)
                                used_types.update(deleter.used_types)
                        elif attr_type is functools.cached_property:
                            used_types.add(functools.cached_property)
                        handled = True
                        break

                if not handled and inspect.isclass(attr):
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
        raw_ann = getattr(mod, "__annotations__", {})
        try:
            resolved_ann = get_type_hints(mod, include_extras=True)
        except Exception:
            resolved_ann = raw_ann

        handled_names: set[str] = set()
        for name, obj in globals_dict.items():
            if resolved_ann.get(name) is typing.TypeAlias:
                fmt = format_type(obj)
                used_types.update(fmt.used)
                body.append(
                    PyiAlias(
                        name=name,
                        value=fmt.text,
                        used_types=fmt.used,
                    )
                )
                continue

            if isinstance(obj, typing.TypeAliasType):
                fmt = format_type(obj.__value__)
                used_types.update(fmt.used)
                params = []
                for tp in getattr(obj, "__type_params__", ()):  # pragma: no cover - py312
                    if isinstance(tp, typing.TypeVar):
                        params.append(tp.__name__)
                    elif isinstance(tp, typing.ParamSpec):
                        params.append(f"**{tp.__name__}")
                    elif isinstance(tp, typing.TypeVarTuple):
                        params.append(f"*{tp.__name__}")
                body.append(
                    PyiAlias(
                        name=name,
                        value=fmt.text,
                        keyword="type",
                        type_params=params,
                        used_types=fmt.used,
                    )
                )
                continue

            if not hasattr(obj, '__module__') or obj.__module__ != mod_name:
                annotation = resolved_ann.get(name)
                if annotation is not None:
                    fmt = format_type(annotation)
                    used_types.update(fmt.used)
                    body.append(
                        PyiVariable(
                            name=name,
                            type_str=fmt.text,
                            used_types=fmt.used,
                        )
                    )
                    handled_names.add(name)
                continue
            if id(obj) in seen:
                continue
            seen[id(obj)] = name
            handled_names.add(name)

            # decorated callables like ``lru_cache`` wrappers are not
            # ``inspect.isfunction`` but expose ``__wrapped__`` with the
            # original function. Unwrap them so they emit correct stubs.
            fn_obj = None
            if inspect.isfunction(obj):
                fn_obj = obj
            elif (
                callable(obj)
                and hasattr(obj, "__wrapped__")
                and inspect.isfunction(obj.__wrapped__)
                and not isinstance(
                    obj,
                    (
                        classmethod,
                        staticmethod,
                        property,
                        functools.cached_property,
                    ),
                )
            ):
                fn_obj = obj.__wrapped__

            if fn_obj is not None:
                if fn_obj.__name__ == "<lambda>":
                    annotation = resolved_ann.get(name)
                    if annotation is not None:
                        fmt = format_type(annotation)
                        used_types.update(fmt.used)
                        body.append(
                            PyiVariable(
                                name=name,
                                type_str=fmt.text,
                                used_types=fmt.used,
                            )
                        )
                    else:
                        body.append(PyiVariable.from_assignment(name, obj))
                    continue

                ovs = _get_overloads(fn_obj)
                if ovs:
                    for ov in ovs:
                        ofunc = PyiFunction.from_function(
                            ov,
                            decorators=["overload"],
                            globalns=globals_dict,
                            localns=globals_dict,
                        )
                        used_types.update(ofunc.used_types)
                        body.append(ofunc)
                else:
                    func = PyiFunction.from_function(
                        fn_obj,
                        globalns=globals_dict,
                        localns=globals_dict,
                    )
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
            else:
                handled = False
                for alias_type in _ALIAS_TYPES:
                    if isinstance(obj, alias_type):
                        alias_used = {alias_type}
                        used_types.update(alias_used)
                        if isinstance(obj, typing.TypeVar):
                            args = [f"'{obj.__name__}'"]
                            if getattr(obj, "__covariant__", False):
                                args.append("covariant=True")
                            if getattr(obj, "__contravariant__", False):
                                args.append("contravariant=True")
                            if getattr(obj, "__infer_variance__", False):
                                args.append("infer_variance=True")
                            value = f"TypeVar({', '.join(args)})"
                        elif isinstance(obj, typing.ParamSpec):
                            args = [f"'{obj.__name__}'"]
                            if getattr(obj, "__covariant__", False):
                                args.append("covariant=True")
                            if getattr(obj, "__contravariant__", False):
                                args.append("contravariant=True")
                            value = f"ParamSpec({', '.join(args)})"
                        else:
                            value = f"{alias_type.__name__}('{obj.__name__}')"
                        body.append(
                            PyiAlias(
                                name=name,
                                value=value,
                                used_types=alias_used,
                            )
                        )
                        handled = True
                        break

                if not handled and isinstance(obj, (int, str, float, bool)):
                    body.append(PyiVariable.from_assignment(name, obj))

        for name, annotation in resolved_ann.items():
            if name not in handled_names and name not in globals_dict:
                if annotation is typing.TypeAlias:
                    continue
                fmt = format_type(annotation)
                used_types.update(fmt.used)
                body.append(
                    PyiVariable(
                        name=name,
                        type_str=fmt.text,
                        used_types=fmt.used,
                    )
                )

        typing_names = sorted(
            t.__name__
            for t in used_types
            if getattr(t, '__module__', '') == 'typing'
            and not isinstance(t, (typing.TypeVar, typing.ParamSpec, typing.TypeVarTuple))
        )

        external_imports: dict[str, set[str]] = collections.defaultdict(set)
        for used_type in used_types:
            modname = getattr(used_type, "__module__", None)
            name = getattr(used_type, "__name__", None)
            if not modname or not name:
                continue
            if modname in ("builtins", "typing", mod_name):
                continue
            external_imports[modname].add(name)

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




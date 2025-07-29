from __future__ import annotations

"""Utilities for building ``.pyi`` objects from live Python modules."""

import abc
import dataclasses
import enum
import functools
import inspect
import types
import typing
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Callable, get_args, get_origin, get_type_hints

_INDENT = "    "

import collections
import collections.abc

_MODULE_ALIASES: dict[str, str] = {
    "pathlib._local": "pathlib",
    "pathlib._pathlib": "pathlib",
}

from .meta_types import get_overloads as _get_overloads


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
    line: int | None = field(default=None, kw_only=True)


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

    if isinstance(type_obj, dataclasses.InitVar):
        used.add(dataclasses.InitVar)
        try:
            inner = type_obj.type
        except Exception:
            inner = None
        if inner is not None:
            inner_fmt = format_type(inner)
            used.update(inner_fmt.used)
            return TypeRenderInfo(f"InitVar[{inner_fmt.text}]", used)
        return TypeRenderInfo("InitVar", used)

    if isinstance(type_obj, typing.ParamSpecArgs):
        base = format_type(type_obj.__origin__)
        used.update(base.used)
        return TypeRenderInfo(f"{base.text}.args", used)

    if isinstance(type_obj, typing.ParamSpecKwargs):
        base = format_type(type_obj.__origin__)
        used.update(base.used)
        return TypeRenderInfo(f"{base.text}.kwargs", used)

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
    if getattr(typing, "LiteralString", None) is not None and type_obj is typing.LiteralString:
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
        origin_name = getattr(origin, "__qualname__", str(origin))
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
        _no_default = getattr(typing, "NoDefault", None)
        if default is not None and (_no_default is None or default is not _no_default):
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
    elif isinstance(type_obj, typing.ParamSpecArgs):
        found.add(f"**{type_obj.__origin__.__name__}")
    elif isinstance(type_obj, typing.ParamSpecKwargs):
        found.add(f"**{type_obj.__origin__.__name__}")
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

# Methods generated by typing.Protocol which should be ignored
_PROTOCOL_METHOD_NAMES = {"_proto_hook", "_no_init_or_replace_init"}

# Mapping of typing alias types to the factory function used to recreate them.
# Types that represent aliases and the factory function used to recreate them
_ALIAS_TYPES: tuple[type, ...] = (
    typing.TypeVarTuple,
    typing.TypeVar,
    typing.ParamSpec,
)


def _unwrap_decorated_function(obj: Any) -> Callable | None:
    """Return the underlying function for *obj* if it is a decorated callable."""

    while True:
        if inspect.isfunction(obj):
            return obj
        if not (
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
            return None
        obj = obj.__wrapped__


def _unwrap_descriptor(obj: Any) -> Any | None:
    """Return the underlying descriptor for *obj* if wrapped by decorators."""

    while True:
        for typ in _ATTR_DECORATORS:
            if isinstance(obj, typ):
                return obj
        if hasattr(obj, "__wrapped__"):
            obj = obj.__wrapped__
            continue
        return None


def _extract_partialmethod(
    pm: functools.partialmethod,
    klass: type,
    name: str,
    *,
    globalns: dict[str, Any],
) -> Callable:
    """Return a function object for ``partialmethod`` *pm* defined on *klass*."""

    fn = pm.__get__(None, klass)
    try:
        hints = get_type_hints(
            pm.func, globalns=globalns, localns=klass.__dict__, include_extras=True
        )
    except Exception:
        hints = getattr(pm.func, "__annotations__", {}).copy()

    sig_params = inspect.signature(fn).parameters
    fn.__annotations__ = {k: v for k, v in hints.items() if k in sig_params or k == "return"}
    fn.__name__ = name
    return fn


def _get_class_function(
    attr: Any,
    name: str,
    klass: type,
    *,
    globalns: dict[str, Any],
) -> Callable | None:
    """Return the underlying function represented by *attr* on *klass*."""

    fn = _unwrap_decorated_function(attr)
    if fn is not None:
        return fn
    if isinstance(attr, functools.partialmethod):
        return _extract_partialmethod(attr, klass, name, globalns=globalns)
    return None


def _dataclass_decorator(klass: type) -> tuple[str, set[type]] | None:
    """Return the ``@dataclass`` decorator text for *klass*."""

    if not (dataclasses.is_dataclass(klass) or hasattr(klass, "__dataclass_fields__")):
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


@dataclass
class PyiAlias(PyiNamedElement):
    value: str
    keyword: str = ""
    type_params: list[str] = field(default_factory=list)

    def render(self, indent: int = 0) -> list[str]:
        """Return the pyi representation for this alias."""

        space = self._space(indent)
        kw = f"{self.keyword} " if self.keyword else ""
        param_str = f"[{', '.join(self.type_params)}]" if self.type_params else ""
        return [f"{space}{kw}{self.name}{param_str} = {self.value}"]


def _collect_args(
    sig: inspect.Signature, hints: dict[str, Any]
) -> tuple[list[tuple[str, str | None]], set[type]]:
    """Return rendered arguments and used types for ``sig``."""

    args: list[tuple[str, str | None]] = []
    used_types: set[type] = set()
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
            if name in {"self", "cls"}:
                ann = None
            else:
                ann = "Any"
                used_types.add(Any)
        else:
            hint = hints.get(name, "Any")
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

    return args, used_types


def _collect_type_params(
    fn: Callable,
    hints: dict[str, Any],
    exclude_params: set[str] | None,
) -> tuple[list[str], set[type]]:
    """Return type parameter strings and used types for ``fn``."""

    tp_strings: list[str] = []
    used: set[type] = set()
    type_param_objs = getattr(fn, "__type_params__", None)
    if type_param_objs:
        for tp in type_param_objs:
            name = tp.__name__
            if exclude_params and name in exclude_params:
                continue
            fmt = format_type_param(tp)
            tp_strings.append(fmt.text)
            used.update(fmt.used)
    else:
        all_types = list(hints.values())
        type_params = sorted(find_typevars(t) for t in all_types)
        flat_params = sorted(set().union(*type_params)) if type_params else []
        if exclude_params:
            flat_params = [p for p in flat_params if p.lstrip("*") not in exclude_params]
        tp_strings = flat_params
    return tp_strings, used


def _collect_decorators(
    decorators: list[str] | None, fn: Callable, *, skip_final: bool = False
) -> tuple[list[str], set[type]]:
    """Return decorator strings and used types for ``fn``."""

    decos = list(decorators or [])
    used: set[type] = set()
    if getattr(fn, "__final__", False) and not skip_final:
        decos.append("final")
        used.add(typing.final)
    if getattr(fn, "__override__", False):
        decos.append("override")
        used.add(getattr(typing, "override"))
    if getattr(fn, "__isabstractmethod__", False):
        decos.append("abstractmethod")
        used.add(abc.abstractmethod)
    if "overload" in decos:
        used.add(typing.overload)
    return decos, used


def _typeddict_info(klass: type) -> tuple[list[type], bool | None]:
    """Return TypedDict base classes and total value for *klass*."""

    if not isinstance(klass, typing._TypedDictMeta):
        return [], None
    bases = [
        b for b in getattr(klass, "__orig_bases__", ()) if isinstance(b, typing._TypedDictMeta)
    ]
    total = klass.__dict__.get("__total__", True) if not bases else None
    return bases, total


def _class_decorators(klass: type) -> tuple[list[str], set[type], bool]:
    """Return decorators, used types and dataclass flag for *klass*."""

    decos: list[str] = []
    used: set[type] = set()
    if getattr(klass, "__final__", False):
        decos.append("final")
        used.add(typing.final)
    if getattr(klass, "_is_runtime_protocol", False):
        decos.append("runtime_checkable")
        used.add(typing.runtime_checkable)

    deco_info = _dataclass_decorator(klass)
    is_dc = deco_info is not None
    if deco_info:
        deco, dec_used = deco_info
        decos.append(deco)
        used.update(dec_used)

    return decos, used, is_dc


def _namedtuple_members(klass: type) -> tuple[list[PyiElement], set[type]]:
    """Return ``PyiVariable`` members for ``NamedTuple`` classes."""

    members: list[PyiElement] = []
    used: set[type] = set()
    raw_ann = klass.__dict__.get("__annotations__", {})
    for name, annotation in raw_ann.items():
        fmt = format_type(annotation)
        members.append(PyiVariable(name=name, type_str=fmt.text, used_types=fmt.used))
        used.update(fmt.used)
    return members, used


def _namedtuple_bases(klass: type, type_params: list[str]) -> tuple[list[str], set[type]]:
    """Return bases and used types for ``NamedTuple`` classes."""

    bases = ["NamedTuple"]
    used: set[type] = {typing.NamedTuple}
    raw_bases = getattr(klass, "__orig_bases__", ())
    for b in raw_bases:
        if get_origin(b) is typing.Generic:
            if not type_params:
                for param in get_args(b):
                    inner = param
                    if get_origin(param) is typing.Unpack:
                        inner = get_args(param)[0]
                    if isinstance(
                        inner,
                        (
                            typing.TypeVar,
                            typing.ParamSpec,
                            typing.TypeVarTuple,
                        ),
                    ):
                        fmt = format_type_param(inner)
                    else:
                        fmt = format_type(param)
                    type_params.append(fmt.text)
                    used.update(fmt.used)
    return bases, used


def _typeddict_bases(klass: type, bases: list[type]) -> tuple[list[str], set[type]]:
    """Return rendered bases and used types for ``TypedDict`` classes."""

    rendered: list[str] = []
    used: set[type] = set()
    for b in bases:
        fmt = format_type(b)
        rendered.append(fmt.text)
        used.update(fmt.used)
    if not rendered:
        rendered = ["TypedDict"]
        used.add(typing.TypedDict)
    return rendered, used


def _normal_class_bases(klass: type, type_params: list[str]) -> tuple[list[str], set[type]]:
    """Return rendered bases and used types for normal classes."""

    raw_bases = getattr(klass, "__orig_bases__", None) or klass.__bases__
    rendered: list[str] = []
    used: set[type] = set()
    for b in raw_bases:
        if b is object:
            continue
        if get_origin(b) is typing.Generic:
            if not type_params:
                for param in get_args(b):
                    inner = param
                    if get_origin(param) is typing.Unpack:
                        inner = get_args(param)[0]
                    if isinstance(
                        inner,
                        (
                            typing.TypeVar,
                            typing.ParamSpec,
                            typing.TypeVarTuple,
                        ),
                    ):
                        fmt = format_type_param(inner)
                    else:
                        fmt = format_type(param)
                    type_params.append(fmt.text)
                    used.update(fmt.used)
            continue
        fmt = format_type(b)
        rendered.append(fmt.text)
        used.update(fmt.used)
    return rendered, used


def _class_variables(
    klass: type,
    *,
    globalns: dict[str, Any],
    is_typeddict: bool,
    td_bases: list[type],
    is_dataclass_obj: bool,
) -> tuple[list[PyiElement], set[type]]:
    """Return ``PyiVariable`` members for ``klass``."""

    raw_ann = klass.__dict__.get("__annotations__", {})
    if is_typeddict:
        base_fields: set[str] = set()
        for b in td_bases:
            base_fields.update(getattr(b, "__annotations__", {}).keys())
        resolved = {n: a for n, a in raw_ann.items() if n not in base_fields}
    else:
        try:
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

    members: list[PyiElement] = []
    used: set[type] = set()
    for name, annotation in resolved.items():
        fmt = format_type(annotation)
        members.append(PyiVariable(name=name, type_str=fmt.text, used_types=fmt.used))
        used.update(fmt.used)
    return members, used


def _enum_members(klass: enum.EnumMeta) -> list[PyiElement]:
    """Return ``PyiAlias`` members for ``Enum`` classes."""

    members: list[PyiElement] = []
    for member_name, member in klass.__members__.items():
        members.append(PyiAlias(name=member_name, value=repr(member.value)))
    return members


def _auto_methods(klass: type, *, is_dataclass_obj: bool, is_enum: bool) -> set[str]:
    """Return the set of method names automatically generated for ``klass``."""

    if is_dataclass_obj:
        params = getattr(klass, "__dataclass_params__", None)
        auto = _dataclass_auto_methods(params)
    else:
        auto = set()
    if is_enum:
        auto.update({"_generate_next_value_", "__new__"})
        for name in ("__repr__", "__str__", "__format__"):
            value = klass.__dict__.get(name)
            if getattr(value, "__module__", None) == "enum":
                auto.add(name)
        if issubclass(klass, enum.Flag):
            auto.update(
                {
                    "__or__",
                    "__and__",
                    "__xor__",
                    "__ror__",
                    "__rand__",
                    "__rxor__",
                    "__invert__",
                }
            )
    return auto


def _protocol_skip_methods(klass: type) -> set[str]:
    """Return method names that should be skipped for ``Protocol`` classes."""

    if getattr(klass, "_is_protocol", False):
        return {"__init__", "__subclasshook__"}
    return set()


def _function_members(
    fn: Callable,
    *,
    class_params: set[str],
    globalns: dict[str, Any],
    localns: dict[str, Any],
) -> tuple[list[PyiFunction], set[type]]:
    """Return ``PyiFunction`` objects for *fn* including overloads."""

    members: list[PyiFunction] = []
    used: set[type] = set()

    ovs = _get_overloads(fn)
    if ovs:
        for ov in ovs:
            func = PyiFunction.from_function(
                ov,
                decorators=["overload"],
                exclude_params=class_params,
                globalns=globalns,
                localns=localns,
            )
            members.append(func)
            used.update(func.used_types)
    else:
        func = PyiFunction.from_function(
            fn,
            exclude_params=class_params,
            globalns=globalns,
            localns=localns,
        )
        members.append(func)
        used.update(func.used_types)
    return members, used


def _descriptor_members(
    attr_name: str,
    attr: Any,
    *,
    class_params: set[str],
    globalns: dict[str, Any],
    localns: dict[str, Any],
) -> tuple[list[PyiElement], set[type]]:
    """Return method objects generated from descriptor *attr*."""
    unwrapped = _unwrap_descriptor(attr) or attr

    for attr_type, (func_attr, deco) in _ATTR_DECORATORS.items():
        if isinstance(unwrapped, attr_type):
            fn_obj = getattr(unwrapped, func_attr)
            for flag in ("__final__", "__override__", "__isabstractmethod__"):
                if getattr(attr, flag, False) and not getattr(fn_obj, flag, False):
                    setattr(fn_obj, flag, True)
            func = PyiFunction.from_function(
                fn_obj,
                decorators=[deco],
                exclude_params=class_params,
                globalns=globalns,
                localns=localns,
            )
            members = [func]
            used = set(func.used_types)
            if attr_type is property:
                if unwrapped.fset is not None:
                    setter = PyiFunction.from_function(
                        unwrapped.fset,
                        decorators=[f"{attr_name}.setter"],
                        exclude_params=class_params,
                        globalns=globalns,
                        localns=localns,
                    )
                    members.append(setter)
                    used.update(setter.used_types)
                if unwrapped.fdel is not None:
                    deleter = PyiFunction.from_function(
                        unwrapped.fdel,
                        decorators=[f"{attr_name}.deleter"],
                        exclude_params=class_params,
                        globalns=globalns,
                        localns=localns,
                    )
                    members.append(deleter)
                    used.update(deleter.used_types)
            elif attr_type is functools.cached_property:
                used.add(functools.cached_property)
            return members, used
    return [], set()


def _class_methods(
    klass: type,
    *,
    globalns: dict[str, Any],
    class_params: set[str],
    is_enum: bool,
    is_dataclass_obj: bool,
) -> tuple[list[PyiElement], set[type]]:
    """Return ``PyiFunction`` members for *klass*."""

    auto_methods = _auto_methods(klass, is_dataclass_obj=is_dataclass_obj, is_enum=is_enum)
    protocol_skip = _protocol_skip_methods(klass)

    members: list[PyiElement] = []
    used: set[type] = set()

    for attr_name, attr in klass.__dict__.items():
        if attr_name in auto_methods:
            continue
        if attr_name in protocol_skip or getattr(attr, "__name__", None) in _PROTOCOL_METHOD_NAMES:
            continue
        fn_attr = _get_class_function(attr, attr_name, klass, globalns=globalns)
        if fn_attr is not None and fn_attr.__name__ != "<lambda>":
            funcs, func_used = _function_members(
                fn_attr,
                class_params=class_params,
                globalns=globalns,
                localns=klass.__dict__,
            )
            members.extend(funcs)
            used.update(func_used)
            continue

        desc_members, desc_used = _descriptor_members(
            attr_name,
            attr,
            class_params=class_params,
            globalns=globalns,
            localns=klass.__dict__,
        )
        if desc_members:
            members.extend(desc_members)
            used.update(desc_used)
            continue

        if inspect.isclass(attr) and attr.__qualname__.startswith(klass.__qualname__ + "."):
            members.append(PyiClass.from_class(attr))

    return members, used


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
        skip_final: bool = False,
        globalns: dict[str, Any] | None = None,
        localns: dict[str, Any] | None = None,
    ) -> PyiFunction:
        """Create a :class:`PyiFunction` from ``fn``."""

        try:
            hints = get_type_hints(fn, globalns=globalns, localns=localns, include_extras=True)
        except Exception:
            hints = {}

        sig = inspect.signature(fn)
        args, used_types = _collect_args(sig, hints)

        if "return" in hints:
            ret_fmt = format_type(hints["return"])
            ret_text = ret_fmt.text
            used_types.update(ret_fmt.used)
        else:
            ret_text = ""

        tp_strings, tp_used = _collect_type_params(fn, hints, exclude_params)
        used_types.update(tp_used)

        decorators, dec_used = _collect_decorators(decorators, fn, skip_final=skip_final)
        used_types.update(dec_used)

        is_async = inspect.iscoroutinefunction(fn) or inspect.isasyncgenfunction(fn)

        return cls(
            name=getattr(fn, "__qualname_override__", fn.__name__),
            args=args,
            return_type=ret_text,
            decorators=decorators,
            type_params=tp_strings,
            used_types=used_types,
            is_async=is_async,
        )


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
        globalns = vars(inspect.getmodule(klass))

        td_bases, typeddict_total = _typeddict_info(klass)
        decorators, used_types, is_dataclass_obj = _class_decorators(klass)
        class_params: set[str] = {t.__name__ for t in getattr(klass, "__parameters__", ())}

        type_params: list[str] = []
        if hasattr(klass, "__type_params__") and klass.__type_params__:
            for tp in klass.__type_params__:
                fmt = format_type_param(tp)
                type_params.append(fmt.text)
                used_types.update(fmt.used)
        elif is_typeddict and getattr(klass, "__parameters__", ()):
            for tp in klass.__parameters__:
                fmt = format_type_param(tp)
                type_params.append(fmt.text)
                used_types.update(fmt.used)

        members: list[PyiElement] = []

        if is_namedtuple:
            bases, base_used = _namedtuple_bases(klass, type_params)
            used_types.update(base_used)
            vars_members, vars_used = _namedtuple_members(klass)
            members.extend(vars_members)
            used_types.update(vars_used)
            return cls(
                name=getattr(klass, "__qualname_override__", klass.__name__),
                bases=bases,
                type_params=type_params,
                body=members,
                typeddict_total=None,
                decorators=decorators,
                used_types=used_types,
            )

        if is_typeddict:
            bases, base_used = _typeddict_bases(klass, td_bases)
        else:
            bases, base_used = _normal_class_bases(klass, type_params)
        used_types.update(base_used)

        vars_members, vars_used = _class_variables(
            klass,
            globalns=globalns,
            is_typeddict=is_typeddict,
            td_bases=td_bases,
            is_dataclass_obj=is_dataclass_obj,
        )
        members.extend(vars_members)
        used_types.update(vars_used)

        if is_enum:
            members.extend(_enum_members(klass))

        if not is_typeddict:
            method_members, method_used = _class_methods(
                klass,
                globalns=globalns,
                class_params=class_params,
                is_enum=is_enum,
                is_dataclass_obj=is_dataclass_obj,
            )
            members.extend(method_members)
            used_types.update(method_used)

        return cls(
            name=getattr(klass, "__qualname_override__", klass.__name__),
            bases=bases,
            type_params=type_params,
            body=members,
            typeddict_total=typeddict_total,
            decorators=decorators,
            used_types=used_types,
        )


class _ModuleBuilder:
    """Helper for building :class:`PyiModule` objects."""

    def __init__(self, mod: ModuleType, line_map: dict[str, int] | None = None) -> None:
        self.mod = mod
        self.mod_name = mod.__name__
        self.globals = vars(mod)
        raw_ann = getattr(mod, "__annotations__", {})
        try:
            self.resolved_ann = get_type_hints(mod, include_extras=True)
        except Exception:
            self.resolved_ann = raw_ann

        self.seen: dict[int, str] = {}
        self.body: list[PyiElement] = []
        self.used_types: set[type] = set()
        self.handled_names: set[str] = set()
        self.line_map = line_map or {}

    # -- helpers -----------------------------------------------------
    def _add(self, item: PyiElement) -> None:
        self.body.append(item)
        self.used_types.update(getattr(item, "used_types", set()))

    def _handle_alias(self, name: str, obj: Any) -> bool:
        if self.resolved_ann.get(name) is typing.TypeAlias:
            if isinstance(obj, str):
                fmt_text = obj
                alias_used: set[type] = set()
            else:
                fmt = format_type(obj)
                fmt_text = fmt.text
                alias_used = fmt.used
            self._add(
                PyiAlias(
                    name=name,
                    value=fmt_text,
                    used_types=alias_used,
                    line=self.line_map.get(name),
                )
            )
            return True

        if isinstance(obj, typing.TypeAliasType):
            fmt = format_type(obj.__value__)
            params = []
            for tp in getattr(obj, "__type_params__", ()):  # pragma: no cover - py312
                if self.globals.get(tp.__name__) is tp:
                    if isinstance(tp, typing.ParamSpec):
                        params.append(f"**{tp.__name__}")
                    elif isinstance(tp, typing.TypeVarTuple):
                        params.append(f"*{tp.__name__}")
                    else:
                        params.append(tp.__name__)
                else:
                    fmt_tp = format_type_param(tp)
                    params.append(fmt_tp.text)
                    self.used_types.update(fmt_tp.used)
            self._add(
                PyiAlias(
                    name=name,
                    value=fmt.text,
                    keyword="type",
                    type_params=params,
                    used_types=fmt.used,
                    line=self.line_map.get(name),
                )
            )
            self.used_types.update(fmt.used)
            return True
        return False

    def _handle_foreign_variable(self, name: str, obj: Any) -> bool:
        annotation = self.resolved_ann.get(name)
        if not hasattr(obj, "__module__"):
            annotation = self.resolved_ann.get(name)
            if annotation is not None:
                fmt = format_type(annotation)
                self._add(
                    PyiVariable(
                        name=name,
                        type_str=fmt.text,
                        used_types=fmt.used,
                        line=self.line_map.get(name),
                    )
                )
            elif isinstance(obj, (int, str, float, bool)):
                var = PyiVariable.from_assignment(name, obj)
                var.line = self.line_map.get(name)
                self._add(var)
            self.handled_names.add(name)
            return True
        if obj.__module__ != self.mod_name:
            if annotation is not None:
                fmt = format_type(annotation)
                self._add(
                    PyiVariable(
                        name=name,
                        type_str=fmt.text,
                        used_types=fmt.used,
                        line=self.line_map.get(name),
                    )
                )
            elif isinstance(obj, (int, str, float, bool)):
                var = PyiVariable.from_assignment(name, obj)
                var.line = self.line_map.get(name)
                self._add(var)
            else:
                alias_name = getattr(obj, "__name__", None)
                if alias_name and alias_name != name:
                    self._add(
                        PyiAlias(
                            name=name,
                            value=alias_name,
                            used_types={obj},
                            line=self.line_map.get(name),
                        )
                    )
            self.handled_names.add(name)
            return True
        return False

    def _handle_function(self, name: str, obj: Any) -> bool:
        fn_obj = _unwrap_decorated_function(obj)
        if fn_obj is None:
            return False

        if fn_obj.__name__ == "<lambda>":
            annotation = self.resolved_ann.get(name)
            if annotation is not None:
                fmt = format_type(annotation)
                self._add(
                    PyiVariable(
                        name=name,
                        type_str=fmt.text,
                        used_types=fmt.used,
                        line=self.line_map.get(name),
                    )
                )
            else:
                var = PyiVariable.from_assignment(name, obj)
                var.line = self.line_map.get(name)
                self._add(var)
            return True

        canonical = getattr(fn_obj, "__qualname_override__", name)
        ovs = _get_overloads(fn_obj)
        if ovs:
            for ov in ovs:
                func = PyiFunction.from_function(
                    ov,
                    decorators=["overload"],
                    skip_final=True,
                    globalns=self.globals,
                    localns=self.globals,
                )
                if func.name != canonical:
                    func.name = canonical
                func.line = self.line_map.get(name)
                self._add(func)
        else:
            func = PyiFunction.from_function(
                fn_obj,
                skip_final=True,
                globalns=self.globals,
                localns=self.globals,
            )
            if func.name != canonical:
                func.name = canonical
            func.line = self.line_map.get(name)
            self._add(func)
        return True

    def _handle_class(self, name: str, obj: Any) -> bool:
        if not inspect.isclass(obj):
            return False
        cls_obj = PyiClass.from_class(obj)
        cls_obj.line = self.line_map.get(name)
        canonical = getattr(obj, "__qualname_override__", name)
        if cls_obj.name != canonical:
            cls_obj.name = canonical
        self._add(cls_obj)
        for item in cls_obj.body:
            if isinstance(item, (PyiFunction, PyiVariable)):
                self.used_types.update(getattr(item, "used_types", set()))
        return True

    def _handle_newtype(self, name: str, obj: Any) -> bool:
        if callable(obj) and hasattr(obj, "__supertype__"):
            base_fmt = format_type(obj.__supertype__)
            alias_used = {typing.NewType, *base_fmt.used}
            self._add(
                PyiAlias(
                    name=name,
                    value=f"NewType('{name}', {base_fmt.text})",
                    used_types=alias_used,
                    line=self.line_map.get(name),
                )
            )
            self.used_types.update(alias_used)
            return True
        return False

    def _handle_alias_types(self, name: str, obj: Any) -> bool:
        for alias_type in _ALIAS_TYPES:
            if isinstance(obj, alias_type):
                alias_used = {alias_type}
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
                self._add(
                    PyiAlias(
                        name=name,
                        value=value,
                        used_types=alias_used,
                        line=self.line_map.get(name),
                    )
                )
                self.used_types.update(alias_used)
                return True
        return False

    def _handle_constant(self, name: str, obj: Any) -> bool:
        if isinstance(obj, (int, str, float, bool)):
            var = PyiVariable.from_assignment(name, obj)
            var.line = self.line_map.get(name)
            self._add(var)
            return True
        return False

    def _process_object(self, name: str, obj: Any) -> None:
        if name.startswith("__") and name.endswith("__"):
            return
        if name == "TYPE_CHECKING":
            return
        canonical = getattr(obj, "__qualname_override__", name)

        if canonical in self.handled_names and id(obj) not in self.seen:
            raise ValueError(f"duplicate emit name: {canonical}")

        if self._handle_alias(name, obj):
            return
        if self._handle_foreign_variable(name, obj):
            return
        if id(obj) in self.seen:
            orig = self.seen[id(obj)]
            if orig != canonical:
                self._add(PyiAlias(name=canonical, value=orig))
            self.handled_names.add(canonical)
            return
        self.seen[id(obj)] = canonical
        self.handled_names.add(canonical)

        if self._handle_function(canonical, obj):
            return
        if self._handle_class(canonical, obj):
            return
        if self._handle_newtype(canonical, obj):
            return
        if self._handle_alias_types(canonical, obj):
            return
        self._handle_constant(canonical, obj)

    def _remaining_annotations(self) -> None:
        for name, annotation in self.resolved_ann.items():
            if name not in self.handled_names and name not in self.globals:
                if annotation is typing.TypeAlias:
                    continue
                fmt = format_type(annotation)
                self._add(
                    PyiVariable(
                        name=name,
                        type_str=fmt.text,
                        used_types=fmt.used,
                        line=self.line_map.get(name),
                    )
                )

    def _imports(self) -> list[str]:
        typing_names = sorted(
            t.__name__
            for t in self.used_types
            if getattr(t, "__module__", "") == "typing"
            and not isinstance(t, (typing.TypeVar, typing.ParamSpec, typing.TypeVarTuple))
        )

        external_imports: dict[str, set[str]] = collections.defaultdict(set)
        for used_type in self.used_types:
            modname = getattr(used_type, "__module__", None)
            modname = _MODULE_ALIASES.get(modname, modname)
            name = getattr(used_type, "__name__", None)
            if not modname or not name:
                continue
            if modname in ("builtins", "typing", self.mod_name):
                continue
            external_imports[modname].add(name)

        lines = []
        if typing_names:
            lines.append(f"from typing import {', '.join(typing_names)}")
        for modname, names in sorted(external_imports.items()):
            lines.append(f"from {modname} import {', '.join(sorted(names))}")
        return lines

    def build(
        self,
        *,
        header_comments: list[str] | None = None,
        comments: dict[int, str] | None = None,
    ) -> "PyiModule":
        for name, obj in self.globals.items():
            self._process_object(name, obj)

        self._remaining_annotations()
        import_lines = self._imports()
        return PyiModule(
            imports=import_lines,
            body=self.body,
            headers=header_comments or [],
            comments=comments or {},
        )


@dataclass
class PyiModule:
    imports: list[str] = field(default_factory=list)
    body: list[PyiElement] = field(default_factory=list)
    headers: list[str] = field(default_factory=list)
    comments: dict[int, str] = field(default_factory=dict)

    def render(self, indent: int = 0) -> list[str]:
        lines: list[str] = []
        if self.headers:
            lines.extend(self.headers)
        lines.extend(self.imports)
        if self.imports:
            lines.append("")
        for item in self.body:
            item_lines = item.render(indent)
            comment = self.comments.get(getattr(item, "line", -1))
            if comment:
                item_lines[0] = f"{item_lines[0]}  {comment}"
            lines.extend(item_lines)
            lines.append("")
        return lines[:-1] if lines and lines[-1] == "" else lines

    @classmethod
    def from_module(cls, mod: ModuleType) -> PyiModule:
        """Create a :class:`PyiModule` from a live module object."""
        comments = getattr(mod, "__macrotype_comments__", {})
        header = getattr(mod, "__macrotype_header_pragmas__", [])
        line_map = getattr(mod, "__macrotype_line_map__", {})
        return _ModuleBuilder(mod, line_map).build(
            header_comments=header, comments=comments
        )

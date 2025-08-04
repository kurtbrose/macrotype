from __future__ import annotations

import collections
import collections.abc
import dataclasses
import enum
import types
import typing
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    ClassVar,
    Generic,
    TypeAliasType,
    TypeVar,
    TypeVarTuple,
    Union,
    get_args,
    get_origin,
)

TypeExpr = Any


class InvalidTypeError(TypeError):
    """Exception raised for invalid typing constructs."""

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        file: str | None = None,
        line: int | None = None,
    ) -> None:
        super().__init__(message)
        self.hint = hint
        self.file = file
        self.line = line

    def __str__(self) -> str:  # pragma: no cover - simple formatting
        location = f"{self.file}:{self.line}: " if self.file and self.line else ""
        hint = f"\nhelp: {self.hint}" if self.hint else ""
        return f"{location}{self.args[0]}{hint}"


class BaseNode:
    """Base class for parsed type nodes."""

    # Registry mapping handled typing "things" to node classes
    _registry: ClassVar[dict[Any, type["BaseNode"]]] = {}

    # Entries this node class handles; subclasses should override
    handles: ClassVar[tuple[Any, ...]] = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for item in getattr(cls, "handles", ()):  # register handled items
            BaseNode._registry[item] = cls

    def emit(self) -> TypeExpr:
        """Return the Python type expression represented by this node."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement emit()")


class TypeExprNode(BaseNode):
    """Type expression that is valid in most contexts."""

    pass


class InClassExprNode(BaseNode):
    """Type expression valid only inside class bodies."""

    pass


class SpecialFormNode(BaseNode):
    """Type expression that is only valid in special contexts."""

    pass


# ``N`` is used by container nodes and aliases to propagate their typing
# context. It can either be the general ``TypeExprNode`` or the superset
# ``InClassExprNode | TypeExprNode`` representing class-body contexts.
N = TypeVar("N", TypeExprNode, InClassExprNode | TypeExprNode)

# ``K`` and ``V`` are used for ``DictNode`` to track key and value contexts
K = TypeVar("K", TypeExprNode, InClassExprNode | TypeExprNode)
V = TypeVar("V", TypeExprNode, InClassExprNode | TypeExprNode)

# ``Ctx`` is used with variadic containers such as ``UnionNode`` and ``TupleNode``.
# Each element corresponds to one argument's context.
Ctx = TypeVarTuple("Ctx")


class ContainerNode(Generic[N], BaseNode):
    """Base class for container nodes."""

    pass


# ``NodeLike`` is either a leaf node or another ``ContainerNode`` with the same
# generic parameter. It reuses the ``N`` type variable so context flows through
# nested containers.
NodeLike = TypeAliasType("NodeLike", N | ContainerNode[N], type_params=(N,))


@dataclass(frozen=True)
class AtomNode(TypeExprNode):
    """Leaf nodes such as ``int`` or ``str``."""

    type_: Any

    def emit(self) -> TypeExpr:
        return self.type_

    @staticmethod
    def is_atom(type_: Any) -> bool:
        atomic_specials = (
            None,
            Ellipsis,
            Any,
            typing.NoReturn,
            typing.Never,
            typing.LiteralString,
        )
        if isinstance(type_, type) and type_ not in {dict, list, tuple, set, frozenset}:
            return True
        if callable(type_) and hasattr(type_, "__supertype__"):
            return True
        if isinstance(
            type_,
            (
                typing.ParamSpecArgs,
                typing.ParamSpecKwargs,
            ),
        ):
            return True
        return type_ in atomic_specials


@dataclass(frozen=True)
class VarNode(TypeExprNode):
    """Node for ``TypeVar``, ``ParamSpec`` and ``TypeVarTuple``."""

    var: typing.TypeVar | typing.ParamSpec | typing.TypeVarTuple

    def emit(self) -> TypeExpr:
        return self.var


@dataclass(frozen=True)
class TypedDictNode(AtomNode):
    """``TypedDict`` leaf node."""

    type_: typing._TypedDictMeta


@dataclass(frozen=True)
class GenericNode(ContainerNode[TypeExprNode]):
    """Node for generics without dedicated handlers."""

    origin: type[Any]
    args: tuple[BaseNode, ...]

    def emit(self) -> TypeExpr:
        return self.origin[tuple(arg.emit() for arg in self.args)]


@dataclass(frozen=True)
class LiteralNode(TypeExprNode):
    handles: ClassVar[tuple[Any, ...]] = (typing.Literal,)
    values: list[int | str | bool | enum.Enum | None]

    def emit(self) -> TypeExpr:
        return typing.Literal[tuple(self.values)]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "LiteralNode":
        validated: list[int | str | bool | enum.Enum | None] = []
        for val in args:
            if val is None or isinstance(val, (int, str, bool, enum.Enum)):
                validated.append(val)
            else:
                raise InvalidTypeError(
                    f"Invalid Literal value: {val!r}",
                    hint="Literal values must be int, str, bool, Enum, or None",
                )
        return cls(values=validated)


@dataclass(frozen=True)
class DictNode(Generic[K, V], ContainerNode[typing.Union[K, V]]):
    handles: ClassVar[tuple[Any, ...]] = (dict,)
    key: NodeLike[K]
    value: NodeLike[V]

    def emit(self) -> TypeExpr:
        return dict[self.key.emit(), self.value.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "DictNode[K, V]":
        if len(args) > 2:
            raise InvalidTypeError(
                f"Too many arguments to dict: {args}",
                hint="dict accepts at most two type arguments",
            )
        key = parse_type(args[0]) if len(args) > 0 else AtomNode(typing.Any)
        val = parse_type(args[1]) if len(args) > 1 else AtomNode(typing.Any)
        return cls(key, val)


@dataclass(frozen=True)
class ListNode(Generic[N], ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]] = (list,)
    element: NodeLike[N]
    container_type: ClassVar[type] = list

    def emit(self) -> TypeExpr:
        return list[self.element.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "ListNode[N]":
        if len(args) > 1:
            raise InvalidTypeError(
                f"Too many arguments to list: {args}",
                hint="list accepts at most one type argument",
            )
        elem = parse_type(args[0]) if args else AtomNode(typing.Any)
        return cls(elem)


@dataclass(frozen=True)
class TupleNode(Generic[*Ctx], ContainerNode[typing.Union[*Ctx]]):
    handles: ClassVar[tuple[Any, ...]] = (tuple,)
    """
    ``tuple[T1, T2, …]`` is class-specific if any element type is. For the
    variadic form ``tuple[T, …]`` we can treat it as ``TupleNode[T]``.
    """

    items: tuple[BaseNode, ...]
    variable: bool = False

    def emit(self) -> TypeExpr:
        args = tuple(item.emit() for item in self.items)
        if self.variable:
            args += (Ellipsis,)
        return tuple[args]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "TupleNode[N]":
        if Ellipsis in args:
            if args[-1] is not Ellipsis or len(args) < 2:
                raise InvalidTypeError(
                    "tuple[T, ...] must have one or more arguments with Ellipsis in final position",
                    hint="Place Ellipsis at the end, e.g. tuple[int, ...]",
                )
            return cls(items=tuple(parse_type(arg) for arg in args[:-1]), variable=True)
        return cls(items=tuple(parse_type(arg) for arg in args), variable=False)


@dataclass(frozen=True)
class SetNode(Generic[N], ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]] = (set,)
    element: NodeLike[N]
    container_type: ClassVar[type] = set

    def emit(self) -> TypeExpr:
        return set[self.element.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "SetNode[N]":
        if len(args) > 1:
            raise InvalidTypeError(
                f"Too many arguments to set: {args}",
                hint="set accepts at most one type argument",
            )
        elem = parse_type(args[0]) if args else AtomNode(typing.Any)
        return cls(elem)


@dataclass(frozen=True)
class FrozenSetNode(Generic[N], ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]] = (frozenset,)
    element: NodeLike[N]
    container_type: ClassVar[type] = frozenset

    def emit(self) -> TypeExpr:
        return frozenset[self.element.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "FrozenSetNode[N]":
        if len(args) > 1:
            raise InvalidTypeError(
                f"Too many arguments to frozenset: {args}",
                hint="frozenset accepts at most one type argument",
            )
        elem = parse_type(args[0]) if args else AtomNode(typing.Any)
        return cls(elem)


@dataclass(frozen=True)
class InitVarNode(SpecialFormNode):
    handles: ClassVar[tuple[Any, ...]] = (dataclasses.InitVar,)
    """``dataclasses.InitVar`` wrapper."""

    inner: TypeExprNode

    def emit(self) -> TypeExpr:
        return dataclasses.InitVar[self.inner.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "InitVarNode":
        if len(args) > 1:
            raise InvalidTypeError(
                f"InitVar takes at most one argument: {args}",
                hint="InitVar[T] accepts a single type argument",
            )
        inner = parse_type_expr(args[0]) if args else AtomNode(typing.Any)
        return cls(inner)


@dataclass(frozen=True)
class SelfNode(InClassExprNode):
    handles: ClassVar[tuple[Any, ...]] = (typing.Self,)
    """``typing.Self`` leaf node."""

    def emit(self) -> TypeExpr:
        return typing.Self

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "SelfNode":
        if args:
            raise InvalidTypeError(
                f"Self takes no arguments: {args}",
                hint="Self should be used without type arguments",
            )
        return cls()


@dataclass(frozen=True)
class ClassVarNode(Generic[N], ContainerNode[N], InClassExprNode):
    handles: ClassVar[tuple[Any, ...]] = (typing.ClassVar,)
    """``typing.ClassVar`` wrapper."""

    inner: NodeLike[N]

    def emit(self) -> TypeExpr:
        return typing.ClassVar[self.inner.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "ClassVarNode[N]":
        if len(args) > 1:
            raise InvalidTypeError(
                f"ClassVar takes at most one argument: {args}",
                hint="ClassVar[T] accepts a single type argument",
            )
        inner = parse_type(args[0]) if args else AtomNode(typing.Any)
        return cls(inner)


@dataclass(frozen=True)
class FinalNode(Generic[N], ContainerNode[N], SpecialFormNode):
    handles: ClassVar[tuple[Any, ...]] = (typing.Final,)
    """``typing.Final`` wrapper."""

    inner: NodeLike[N]

    def emit(self) -> TypeExpr:
        return typing.Final[self.inner.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "FinalNode[N]":
        if len(args) > 1:
            raise InvalidTypeError(
                f"Final takes at most one argument: {args}",
                hint="Final[T] accepts a single type argument",
            )
        inner = parse_type(args[0]) if args else AtomNode(typing.Any)
        return cls(inner)


@dataclass(frozen=True)
class RequiredNode(Generic[N], ContainerNode[N], InClassExprNode):
    handles: ClassVar[tuple[Any, ...]] = (typing.Required,)
    """``typing.Required`` wrapper."""

    inner: NodeLike[N]

    def emit(self) -> TypeExpr:
        return typing.Required[self.inner.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "RequiredNode[N]":
        if len(args) != 1:
            raise InvalidTypeError(
                f"Required requires a single argument: {args}",
                hint="Required[T] expects exactly one argument",
            )
        return cls(parse_type(args[0]))


@dataclass(frozen=True)
class NotRequiredNode(Generic[N], ContainerNode[N], InClassExprNode):
    handles: ClassVar[tuple[Any, ...]] = (typing.NotRequired,)
    """``typing.NotRequired`` wrapper."""

    inner: NodeLike[N]

    def emit(self) -> TypeExpr:
        return typing.NotRequired[self.inner.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "NotRequiredNode[N]":
        if len(args) != 1:
            raise InvalidTypeError(
                f"NotRequired requires a single argument: {args}",
                hint="NotRequired[T] expects exactly one argument",
            )
        return cls(parse_type(args[0]))


@dataclass(frozen=True)
class TypeGuardNode(Generic[N], ContainerNode[N], SpecialFormNode):
    handles: ClassVar[tuple[Any, ...]] = (typing.TypeGuard,)
    """``typing.TypeGuard`` wrapper."""

    target: NodeLike[N]

    def emit(self) -> TypeExpr:
        return typing.TypeGuard[self.target.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "TypeGuardNode[N]":
        if len(args) != 1:
            raise InvalidTypeError(
                f"TypeGuard requires a single argument: {args}",
                hint="TypeGuard[T] expects exactly one argument",
            )
        return cls(parse_type(args[0]))


@dataclass(frozen=True)
class AnnotatedNode(Generic[N], ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]] = (typing.Annotated,)
    base: NodeLike[N]
    metadata: list[Any]

    def emit(self) -> TypeExpr:
        return typing.Annotated[self.base.emit(), *self.metadata]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "AnnotatedNode[N]":
        if not args:
            raise InvalidTypeError(
                "Annotated requires a base type",
                hint="Annotated[T, ...] must start with a type",
            )
        if len(args) < 2:
            raise InvalidTypeError(
                f"Annotated requires a type and at least one annotation: {args}",
                hint="Use Annotated[T, ...] with at least one metadata value",
            )
        base = parse_type(args[0])
        return cls(base, list(args[1:]))


@dataclass(frozen=True)
class ConcatenateNode(Generic[N], ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]] = (typing.Concatenate,)
    parts: list[NodeLike[N]]

    def emit(self) -> TypeExpr:
        return typing.Concatenate[tuple(part.emit() for part in self.parts)]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "ConcatenateNode[N]":
        if not args:
            raise InvalidTypeError(
                "Concatenate requires at least one argument",
                hint="Concatenate[T, ..., P] expects one or more types ending with a ParamSpec or ...",
            )
        last = args[-1]
        if not (isinstance(last, typing.ParamSpec) or last is Ellipsis):
            raise InvalidTypeError(
                f"Concatenate last argument must be a ParamSpec or ellipsis: {last!r}",
                hint="Use a ParamSpec variable or ... as the final argument",
            )
        return cls([parse_type(arg) for arg in args])


@dataclass(frozen=True)
class CallableNode(Generic[N], ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]] = (collections.abc.Callable,)
    args: NodeLike[N] | list[NodeLike[N]] | None
    return_type: NodeLike[N]

    def emit(self) -> TypeExpr:
        if self.args is None:
            return typing.Callable[..., self.return_type.emit()]
        if isinstance(self.args, list):
            return typing.Callable[[a.emit() for a in self.args], self.return_type.emit()]
        return typing.Callable[self.args.emit(), self.return_type.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "CallableNode[N]":
        if not args:
            return cls(args=None, return_type=AtomNode(typing.Any))
        if len(args) != 2:
            raise InvalidTypeError(
                f"Callable arguments invalid: {args}",
                hint="Use Callable[[Arg, ...], Return]",
            )
        arg_list, ret = args
        ret_node = parse_type(ret)
        if arg_list is Ellipsis:
            return cls(args=None, return_type=ret_node)
        if isinstance(arg_list, typing.ParamSpec) or get_origin(arg_list) is typing.Concatenate:
            return cls(parse_type(arg_list), return_type=ret_node)
        return cls([parse_type(a) for a in arg_list], return_type=ret_node)


@dataclass(frozen=True)
class UnionNode(Generic[*Ctx], ContainerNode[typing.Union[*Ctx]]):
    handles: ClassVar[tuple[Any, ...]] = (Union, types.UnionType)
    """A ``typing.Union`` wrapper that is class-specific iff *any* arm is."""

    # The concrete nodes that correspond to each context in ``*Ctx``.
    options: tuple[BaseNode, ...]

    def emit(self) -> TypeExpr:
        return Union[tuple(opt.emit() for opt in self.options)]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "UnionNode[*Ctx]":
        return cls(tuple(parse_type(arg) for arg in args))


@dataclass(frozen=True)
class UnpackNode(SpecialFormNode):
    handles: ClassVar[tuple[Any, ...]] = (typing.Unpack,)
    """``typing.Unpack`` wrapper."""

    target: TupleNode | TypedDictNode | AtomNode | VarNode

    def emit(self) -> TypeExpr:
        return typing.Unpack[self.target.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "UnpackNode":
        if len(args) != 1:
            raise InvalidTypeError(
                f"Unpack requires a single argument: {args}",
                hint="Unpack[T] expects exactly one argument",
            )

        target_raw = args[0]
        target_node = parse_type_expr(target_raw)

        if isinstance(target_node, (TupleNode, TypedDictNode)):
            return cls(target_node)

        if isinstance(target_node, VarNode) and isinstance(target_node.var, typing.TypeVarTuple):
            return cls(target_node)

        raise InvalidTypeError(
            f"Invalid target for Unpack: {target_raw!r}",
            hint="Unpack can target TypeVar or container types",
        )


def _parse_no_origin_type(typ: Any) -> BaseNode:
    if isinstance(typ, (typing.TypeVar, typing.ParamSpec, typing.TypeVarTuple)):
        return VarNode(typ)
    if isinstance(typ, TypeAliasType):
        return parse_type(typ.__value__)
    node_cls = BaseNode._registry.get(typ)
    if node_cls is not None:
        if node_cls is TupleNode:
            return TupleNode((AtomNode(typing.Any),), True)
        return node_cls.for_args(())
    if isinstance(typ, typing._TypedDictMeta):
        return TypedDictNode(typ)
    if isinstance(typ, dataclasses.InitVar):
        return InitVarNode.for_args((typ.type,))
    if AtomNode.is_atom(typ):
        return AtomNode(typ)
    raise InvalidTypeError(
        f"Unrecognized type annotation: {typ!r}",
        hint="Use a valid type or typing construct",
    )


def _parse_origin_type(origin: Any, args: tuple[Any, ...], raw: Any) -> BaseNode:
    node_cls = BaseNode._registry.get(origin)
    if node_cls is not None:
        return node_cls.for_args(args)
    if args and (
        (isinstance(origin, type) and issubclass(origin, typing.Generic))
        or hasattr(origin, "__parameters__")
        or hasattr(raw, "__parameters__")
    ):
        return GenericNode(origin, tuple(parse_type(a) for a in args))
    raise InvalidTypeError(
        f"Unsupported type annotation: {raw!r}",
        hint="Use a supported generic type or typing construct",
    )


_on_generic_callback: Callable[[GenericNode], BaseNode] | None = None


def parse_type(
    typ: Any, *, on_generic: Callable[[GenericNode], BaseNode] | None = None
) -> BaseNode:
    """Parse *typ* into a :class:`BaseNode`.

    If *on_generic* is provided, it will be invoked with any ``GenericNode``
    produced during parsing, allowing custom post-processing of generic types.
    """

    global _on_generic_callback
    prev = _on_generic_callback
    if on_generic is not None:
        _on_generic_callback = on_generic
    try:
        if isinstance(typ, (typing.ParamSpecArgs, typing.ParamSpecKwargs)):
            node = AtomNode(typ)
        else:
            origin = get_origin(typ)
            if origin is None:
                node = _parse_no_origin_type(typ)
            else:
                node = _parse_origin_type(origin, get_args(typ), typ)
        if isinstance(node, GenericNode) and _on_generic_callback is not None:
            return _on_generic_callback(node)
        return node
    finally:
        if on_generic is not None:
            _on_generic_callback = prev


def parse_type_expr(typ: Any) -> TypeExprNode:
    """Parse *typ* ensuring it is a :class:`TypeExprNode`."""

    node = parse_type(typ)
    _reject_special(node)
    return typing.cast(TypeExprNode, node)


def _reject_special(node: BaseNode) -> None:
    """Recursively reject special-form or in-class nodes."""

    if isinstance(node, (SpecialFormNode, InClassExprNode)):
        raise InvalidTypeError(
            "Special form not allowed in this context",
            hint="Use this type only in valid contexts",
        )

    if dataclasses.is_dataclass(node):
        for field in dataclasses.fields(node):
            value = getattr(node, field.name)
            if isinstance(value, BaseNode):
                _reject_special(value)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, BaseNode):
                        _reject_special(item)


@dataclass
class TypeRenderInfo:
    """Formatted representation of a type along with the used types."""

    text: str
    used: set[type]


def _format_node(node: BaseNode) -> TypeRenderInfo:
    return format_type(node.emit(), _skip_parse=True)


def _format_runtime_type(type_obj: Any) -> TypeRenderInfo:
    """Return ``TypeRenderInfo`` for *type_obj* using runtime inspection."""

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
        node = parse_type(type_obj)
        assert isinstance(node, AnnotatedNode)
        base_fmt = format_type(node.base.emit())
        used.add(typing.Annotated)
        used.update(base_fmt.used)
        metadata_str = ", ".join(repr(m) for m in node.metadata)
        return TypeRenderInfo(f"Annotated[{base_fmt.text}, {metadata_str}]", used)

    if origin is typing.Literal:
        used.add(typing.Literal)
        values = ", ".join(repr(a) for a in args)
        return TypeRenderInfo(f"Literal[{values}]", used)

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
        try:
            arg_iter = list(type_obj.__args__)
        except TypeError:
            arg_iter = []
        if arg_iter:
            arg_strs = [format_type(a) for a in arg_iter]
            used.update(*(a.used for a in arg_strs))
            args_str = ", ".join(a.text for a in arg_strs)
            return TypeRenderInfo(f"{type_obj.__class__.__name__}[{args_str}]", used)

    if isinstance(type_obj, type):
        used.add(type_obj)
        return TypeRenderInfo(type_obj.__name__, used)
    if hasattr(type_obj, "_name") and type_obj._name:
        return TypeRenderInfo(type_obj._name, used)

    return TypeRenderInfo(repr(type_obj), used)


def format_type(type_obj: Any, *, _skip_parse: bool = False) -> TypeRenderInfo:
    """Return a ``TypeRenderInfo`` instance for ``type_obj``."""

    if not _skip_parse:
        try:
            node = parse_type(type_obj)
        except InvalidTypeError:
            raise
        except Exception:
            node = None
        else:
            try:
                return _format_node(node)
            except NotImplementedError:
                pass
    return _format_runtime_type(type_obj)


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

    def _collect(node: Any) -> None:
        if isinstance(node, VarNode):
            typ = node.var
            if isinstance(typ, typing.TypeVar):
                found.add(typ.__name__)
            elif isinstance(typ, typing.ParamSpec):
                found.add(f"**{typ.__name__}")
            elif isinstance(typ, typing.TypeVarTuple):
                found.add(f"*{typ.__name__}")
        elif isinstance(node, AtomNode):
            typ = node.type_
            if isinstance(typ, typing.ParamSpecArgs):
                found.add(f"**{typ.__origin__.__name__}")
            elif isinstance(typ, typing.ParamSpecKwargs):
                found.add(f"**{typ.__origin__.__name__}")
        else:
            if dataclasses.is_dataclass(node):
                for field in dataclasses.fields(node):
                    value = getattr(node, field.name)
                    if isinstance(value, BaseNode):
                        _collect(value)
                    elif isinstance(value, (list, tuple)):
                        for item in value:
                            if isinstance(item, BaseNode):
                                _collect(item)

    def _fallback(t: Any) -> set[str]:
        collected: set[str] = set()
        if isinstance(t, typing.TypeVar):
            collected.add(t.__name__)
        elif isinstance(t, typing.ParamSpec):
            collected.add(f"**{t.__name__}")
        elif isinstance(t, typing.ParamSpecArgs):
            collected.add(f"**{t.__origin__.__name__}")
        elif isinstance(t, typing.ParamSpecKwargs):
            collected.add(f"**{t.__origin__.__name__}")
        elif isinstance(t, typing.TypeVarTuple):
            collected.add(f"*{t.__name__}")
        elif hasattr(t, "__parameters__"):
            for p in t.__parameters__:
                collected.update(_fallback(p))
        elif hasattr(t, "__args__"):
            for a in t.__args__:
                collected.update(_fallback(a))
        return collected

    try:
        node = parse_type(type_obj)
    except Exception:
        return _fallback(type_obj)

    found: set[str] = set()
    _collect(node)
    return found

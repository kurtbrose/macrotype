from __future__ import annotations

import collections.abc
import dataclasses
import enum
import typing
from dataclasses import dataclass
from typing import (
    Any,
    ClassVar,
    Generic,
    TypeAliasType,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

TypeExpr = Any


class BaseNode:
    """Base class for parsed type nodes."""

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
        return (
            isinstance(type_, type) and type_ not in {dict, list, tuple, set, frozenset}
        ) or type_ in (None, Ellipsis, Any)


@dataclass(frozen=True)
class TypedDictNode(AtomNode):
    """``TypedDict`` leaf node."""

    type_: typing._TypedDictMeta


@dataclass(frozen=True)
class LiteralNode(TypeExprNode):
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
                raise TypeError(f"Invalid Literal value: {val!r}")
        return cls(values=validated)


@dataclass(frozen=True)
class DictNode(Generic[N], ContainerNode[N]):
    key: NodeLike[N]
    value: NodeLike[N]

    def emit(self) -> TypeExpr:
        return dict[self.key.emit(), self.value.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "DictNode[N]":
        if len(args) > 2:
            raise TypeError(f"Too many arguments to dict: {args}")
        key = parse_type(args[0]) if len(args) > 0 else AtomNode(typing.Any)
        val = parse_type(args[1]) if len(args) > 1 else AtomNode(typing.Any)
        return cls(key, val)


@dataclass(frozen=True)
class ListNode(Generic[N], ContainerNode[N]):
    element: NodeLike[N]
    container_type: ClassVar[type] = list

    def emit(self) -> TypeExpr:
        return list[self.element.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "ListNode[N]":
        if len(args) > 1:
            raise TypeError(f"Too many arguments to list: {args}")
        elem = parse_type(args[0]) if args else AtomNode(typing.Any)
        return cls(elem)


@dataclass(frozen=True)
class TupleNode(Generic[N], ContainerNode[N]):
    items: list[NodeLike[N]]
    variable: bool = False

    def emit(self) -> TypeExpr:
        args = tuple(item.emit() for item in self.items)
        if self.variable:
            args += (Ellipsis,)
        return tuple[args]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "TupleNode[N]":
        variable = False
        if args:
            if args[-1] is Ellipsis:
                variable = True
                args = args[:-1]
            if Ellipsis in args:
                raise TypeError("Ellipsis only allowed in final position of tuple[]")
        return cls([parse_type(arg) for arg in args], variable=variable)


@dataclass(frozen=True)
class SetNode(Generic[N], ContainerNode[N]):
    element: NodeLike[N]
    container_type: ClassVar[type] = set

    def emit(self) -> TypeExpr:
        return set[self.element.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "SetNode[N]":
        if len(args) > 1:
            raise TypeError(f"Too many arguments to set: {args}")
        elem = parse_type(args[0]) if args else AtomNode(typing.Any)
        return cls(elem)


@dataclass(frozen=True)
class FrozenSetNode(Generic[N], ContainerNode[N]):
    element: NodeLike[N]
    container_type: ClassVar[type] = frozenset

    def emit(self) -> TypeExpr:
        return frozenset[self.element.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "FrozenSetNode[N]":
        if len(args) > 1:
            raise TypeError(f"Too many arguments to frozenset: {args}")
        elem = parse_type(args[0]) if args else AtomNode(typing.Any)
        return cls(elem)


@dataclass(frozen=True)
class InitVarNode(SpecialFormNode):
    """``dataclasses.InitVar`` wrapper."""

    inner: TypeExprNode

    def emit(self) -> TypeExpr:
        return dataclasses.InitVar[self.inner.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "InitVarNode":
        if len(args) > 1:
            raise TypeError(f"InitVar takes at most one argument: {args}")
        inner = parse_type_expr(args[0]) if args else AtomNode(typing.Any)
        return cls(inner)


@dataclass(frozen=True)
class SelfNode(InClassExprNode):
    """``typing.Self`` leaf node."""

    def emit(self) -> TypeExpr:
        return typing.Self

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "SelfNode":
        if args:
            raise TypeError(f"Self takes no arguments: {args}")
        return cls()


@dataclass(frozen=True)
class AnnotatedNode(Generic[N], ContainerNode[N]):
    base: NodeLike[N]
    metadata: list[Any]

    def emit(self) -> TypeExpr:
        return typing.Annotated[self.base.emit(), *self.metadata]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "AnnotatedNode[N]":
        if not args:
            raise TypeError("Annotated requires a base type")
        base = parse_type(args[0])
        return cls(base, list(args[1:]))


@dataclass(frozen=True)
class CallableNode(Generic[N], ContainerNode[N]):
    args: list[NodeLike[N]] | None
    return_type: NodeLike[N]

    def emit(self) -> TypeExpr:
        if self.args is None:
            return typing.Callable[..., self.return_type.emit()]
        return typing.Callable[[a.emit() for a in self.args], self.return_type.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "CallableNode[N]":
        if not args:
            return cls(args=None, return_type=AtomNode(typing.Any))
        if len(args) != 2:
            raise TypeError(f"Callable arguments invalid: {args}")
        arg_list, ret = args
        ret_node = parse_type(ret)
        if arg_list is Ellipsis:
            return cls(args=None, return_type=ret_node)
        return cls([parse_type(a) for a in arg_list], return_type=ret_node)


@dataclass(frozen=True)
class UnionNode(Generic[N], ContainerNode[N]):
    options: list[NodeLike[N]]

    def emit(self) -> TypeExpr:
        return Union[tuple(opt.emit() for opt in self.options)]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "UnionNode[N]":
        return cls([parse_type(arg) for arg in args])


@dataclass(frozen=True)
class UnpackNode(SpecialFormNode):
    """``typing.Unpack`` wrapper."""

    target: TupleNode | TypedDictNode

    def emit(self) -> TypeExpr:
        return typing.Unpack[self.target.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "UnpackNode":
        if len(args) != 1:
            raise TypeError(f"Unpack requires a single argument: {args}")

        target_raw = args[0]
        target_node = parse_type_expr(target_raw)

        if isinstance(target_node, TupleNode):
            return cls(target_node)

        if isinstance(target_node, TypedDictNode):
            return cls(target_node)

        raise TypeError(f"Invalid target for Unpack: {target_raw!r}")


def parse_type(typ: Any) -> BaseNode:
    """Parse *typ* into a :class:`BaseNode`."""

    origin = get_origin(typ)
    args = get_args(typ)

    node_map: dict[Any, type[BaseNode]] = {
        typing.Literal: LiteralNode,
        dict: DictNode,
        list: ListNode,
        tuple: TupleNode,
        collections.abc.Callable: CallableNode,
        set: SetNode,
        frozenset: FrozenSetNode,
        dataclasses.InitVar: InitVarNode,
        typing.Annotated: AnnotatedNode,
        typing.Self: SelfNode,
        Union: UnionNode,
        typing.Unpack: UnpackNode,
    }

    if origin is None:
        node_cls = node_map.get(typ)
        if node_cls is not None:
            if node_cls is TupleNode:
                return TupleNode([AtomNode(typing.Any)], variable=True)
            return node_cls.for_args(())
        if isinstance(typ, typing._TypedDictMeta):
            return TypedDictNode(typ)
        if isinstance(typ, dataclasses.InitVar):
            return InitVarNode.for_args((typ.type,))
        if AtomNode.is_atom(typ):
            return AtomNode(typ)
        raise TypeError(f"Unrecognized type atom: {typ!r}")

    node_cls = node_map.get(origin)
    if node_cls is not None:
        return node_cls.for_args(args)

    raise NotImplementedError(f"Unsupported type origin: {origin!r} with args {args!r}")


def parse_type_expr(typ: Any) -> TypeExprNode:
    """Parse *typ* ensuring it is a :class:`TypeExprNode`."""

    node = parse_type(typ)
    _reject_special(node)
    return typing.cast(TypeExprNode, node)


def _reject_special(node: BaseNode) -> None:
    """Recursively reject special-form or in-class nodes."""

    if isinstance(node, (SpecialFormNode, InClassExprNode)):
        raise TypeError("Special form not allowed in this context")

    if isinstance(node, (ListNode, SetNode, FrozenSetNode)):
        _reject_special(node.element)
    elif isinstance(node, DictNode):
        _reject_special(node.key)
        _reject_special(node.value)
    elif isinstance(node, TupleNode):
        for item in node.items:
            _reject_special(item)
    elif isinstance(node, CallableNode):
        if node.args is not None:
            for arg in node.args:
                _reject_special(arg)
        _reject_special(node.return_type)
    elif isinstance(node, AnnotatedNode):
        _reject_special(node.base)
    elif isinstance(node, UnionNode):
        for opt in node.options:
            _reject_special(opt)
    elif isinstance(node, UnpackNode):
        _reject_special(node.target)
    elif isinstance(node, InitVarNode):
        _reject_special(node.inner)

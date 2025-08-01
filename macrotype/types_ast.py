from __future__ import annotations

import collections.abc
import enum
import typing
from dataclasses import dataclass
from typing import Any, ClassVar, Union, get_args, get_origin

TypeExpr = Any


class TypeNode:
    """Base class for parsed type nodes."""

    def emit(self) -> TypeExpr:
        """Return the Python type expression represented by this node."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement emit()")


class TypeExprNode(TypeNode):
    """Type expression that is valid in most contexts."""

    pass


class SpecialFormNode(TypeNode):
    """Type expression that is only valid in special contexts."""

    pass


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
class DictNode(TypeExprNode):
    key_type: TypeExprNode
    value_type: TypeExprNode

    def emit(self) -> TypeExpr:
        return dict[self.key_type.emit(), self.value_type.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "DictNode":
        if len(args) > 2:
            raise TypeError(f"Too many arguments to dict: {args}")
        key = parse_type_expr(args[0]) if len(args) > 0 else AtomNode(typing.Any)
        val = parse_type_expr(args[1]) if len(args) > 1 else AtomNode(typing.Any)
        return cls(key_type=key, value_type=val)


@dataclass(frozen=True)
class ContainerNode(TypeExprNode):
    """Base class for simple container types like ``list`` or ``set``."""

    element_type: TypeExprNode
    container_type: ClassVar[type]

    def emit(self) -> TypeExpr:
        return self.container_type[self.element_type.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "ContainerNode":
        if len(args) > 1:
            raise TypeError(f"Too many arguments to {cls.container_type.__name__}: {args}")
        elem = parse_type_expr(args[0]) if args else AtomNode(typing.Any)
        return cls(elem)


@dataclass(frozen=True)
class ListNode(ContainerNode):
    container_type: ClassVar[type] = list


@dataclass(frozen=True)
class TupleNode(TypeExprNode):
    items: list[TypeExprNode]
    variable: bool = False

    def emit(self) -> TypeExpr:
        args = tuple(item.emit() for item in self.items)
        if self.variable:
            args += (Ellipsis,)
        return tuple[args]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "TupleNode":
        variable = False
        if args:
            if args[-1] is Ellipsis:
                variable = True
                args = args[:-1]
            if Ellipsis in args:
                raise TypeError("Ellipsis only allowed in final position of tuple[]")
        return cls([parse_type_expr(arg) for arg in args], variable=variable)


@dataclass(frozen=True)
class SetNode(ContainerNode):
    container_type: ClassVar[type] = set


@dataclass(frozen=True)
class FrozenSetNode(ContainerNode):
    container_type: ClassVar[type] = frozenset


@dataclass(frozen=True)
class AnnotatedNode(TypeExprNode):
    base: TypeExprNode
    metadata: list[Any]

    def emit(self) -> TypeExpr:
        return typing.Annotated[self.base.emit(), *self.metadata]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "AnnotatedNode":
        if not args:
            raise TypeError("Annotated requires a base type")
        base = parse_type_expr(args[0])
        return cls(base, list(args[1:]))


@dataclass(frozen=True)
class CallableNode(TypeExprNode):
    args: list[TypeExprNode] | None
    return_type: TypeExprNode

    def emit(self) -> TypeExpr:
        if self.args is None:
            return typing.Callable[..., self.return_type.emit()]
        return typing.Callable[[a.emit() for a in self.args], self.return_type.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "CallableNode":
        if not args:
            return cls(args=None, return_type=AtomNode(typing.Any))
        if len(args) != 2:
            raise TypeError(f"Callable arguments invalid: {args}")
        arg_list, ret = args
        ret_node = parse_type_expr(ret)
        if arg_list is Ellipsis:
            return cls(args=None, return_type=ret_node)
        return cls([parse_type_expr(a) for a in arg_list], return_type=ret_node)


@dataclass(frozen=True)
class UnionNode(TypeExprNode):
    options: list[TypeExprNode]

    def emit(self) -> TypeExpr:
        return Union[tuple(opt.emit() for opt in self.options)]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "UnionNode":
        return cls([parse_type_expr(arg) for arg in args])


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


def parse_type(typ: Any) -> TypeExprNode | SpecialFormNode:
    """Parse *typ* into a :class:`TypeNode`."""

    origin = get_origin(typ)
    args = get_args(typ)

    node_map: dict[Any, type[TypeNode]] = {
        typing.Literal: LiteralNode,
        dict: DictNode,
        list: ListNode,
        tuple: TupleNode,
        collections.abc.Callable: CallableNode,
        set: SetNode,
        frozenset: FrozenSetNode,
        typing.Annotated: AnnotatedNode,
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
    if isinstance(node, SpecialFormNode):
        raise TypeError(f"Special form not allowed in this context: {typ!r}")
    return node

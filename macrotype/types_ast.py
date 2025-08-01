from __future__ import annotations

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


@dataclass(frozen=True)
class AtomNode(TypeNode):
    """Leaf nodes such as ``int`` or ``str``."""

    type_: Any

    def emit(self) -> TypeExpr:
        return self.type_

    @staticmethod
    def is_atom(type_: Any) -> bool:
        return isinstance(type_, type) or type_ in (None, Ellipsis, Any)


@dataclass(frozen=True)
class LiteralNode(TypeNode):
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
class DictNode(TypeNode):
    key_type: TypeNode
    value_type: TypeNode

    def emit(self) -> TypeExpr:
        return dict[self.key_type.emit(), self.value_type.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "DictNode":
        if len(args) > 2:
            raise TypeError(f"Too many arguments to dict: {args}")
        key = parse_type(args[0]) if len(args) > 0 else AtomNode(typing.Any)
        val = parse_type(args[1]) if len(args) > 1 else AtomNode(typing.Any)
        return cls(key_type=key, value_type=val)


@dataclass(frozen=True)
class ContainerNode(TypeNode):
    """Base class for simple container types like ``list`` or ``set``."""

    element_type: TypeNode
    container_type: ClassVar[type]

    def emit(self) -> TypeExpr:
        return self.container_type[self.element_type.emit()]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "ContainerNode":
        if len(args) > 1:
            raise TypeError(f"Too many arguments to {cls.container_type.__name__}: {args}")
        elem = parse_type(args[0]) if args else AtomNode(typing.Any)
        return cls(elem)


@dataclass(frozen=True)
class ListNode(ContainerNode):
    container_type: ClassVar[type] = list


@dataclass(frozen=True)
class TupleNode(TypeNode):
    items: list[TypeNode]
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
        return cls([parse_type(arg) for arg in args], variable=variable)


@dataclass(frozen=True)
class SetNode(ContainerNode):
    container_type: ClassVar[type] = set


@dataclass(frozen=True)
class FrozenSetNode(ContainerNode):
    container_type: ClassVar[type] = frozenset


@dataclass(frozen=True)
class UnionNode(TypeNode):
    options: list[TypeNode]

    def emit(self) -> TypeExpr:
        return Union[tuple(opt.emit() for opt in self.options)]

    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> "UnionNode":
        return cls([parse_type(arg) for arg in args])


def parse_type(typ: Any) -> TypeNode:
    """Parse *typ* into a :class:`TypeNode`."""

    origin = get_origin(typ)
    args = get_args(typ)

    if origin is None:
        if AtomNode.is_atom(typ):
            return AtomNode(typ)
        raise TypeError(f"Unrecognized type atom: {typ!r}")

    node_map: dict[Any, type[TypeNode]] = {
        typing.Literal: LiteralNode,
        dict: DictNode,
        list: ListNode,
        tuple: TupleNode,
        set: SetNode,
        frozenset: FrozenSetNode,
        Union: UnionNode,
    }
    node_cls = node_map.get(origin)
    if node_cls is not None:
        return node_cls.for_args(args)

    raise NotImplementedError(f"Unsupported type origin: {origin!r} with args {args!r}")

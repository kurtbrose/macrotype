from __future__ import annotations

import enum
import typing
from dataclasses import dataclass
from typing import Any, Union, get_args, get_origin

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

    if origin is typing.Literal:
        return LiteralNode.for_args(args)
    if origin is dict:
        return DictNode.for_args(args)
    if origin is Union:
        return UnionNode.for_args(args)

    raise NotImplementedError(f"Unsupported type origin: {origin!r} with args {args!r}")

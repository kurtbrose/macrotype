# Generated via: macrotype macrotype -o /tmp/tmp.swm0snV22p
# Do not edit by hand
from typing import Any, ClassVar, ParamSpec, TypeVar, TypeVarTuple, Unpack, _TypedDictMeta
from dataclasses import dataclass
from enum import Enum

TypeExpr = Any

class BaseNode:
    _registry: ClassVar[dict[Any, type[BaseNode]]]
    handles: ClassVar[tuple[Any, ...]]
    @classmethod
    def __init_subclass__(cls, **kwargs: Any) -> None: ...
    def emit(self) -> Any: ...

class TypeExprNode(BaseNode):
    pass

class InClassExprNode(BaseNode):
    pass

class SpecialFormNode(BaseNode):
    pass

N = TypeVar('N')

K = TypeVar('K')

V = TypeVar('V')

Ctx = TypeVarTuple('Ctx')

class ContainerNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](BaseNode):
    pass

type NodeLike[N] = N | ContainerNode[N]

@dataclass(frozen=True)
class AtomNode(TypeExprNode):
    type_: Any
    def emit(self) -> Any: ...
    @staticmethod
    def is_atom(type_: Any) -> bool: ...

@dataclass(frozen=True)
class VarNode(TypeExprNode):
    var: TypeVar | ParamSpec | TypeVarTuple
    def emit(self) -> Any: ...

@dataclass(frozen=True)
class TypedDictNode(AtomNode):
    type_: _TypedDictMeta

@dataclass(frozen=True)
class LiteralNode(TypeExprNode):
    handles: ClassVar[tuple[Any, ...]]
    values: list[int | str | bool | Enum | None]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> LiteralNode: ...

@dataclass(frozen=True)
class DictNode[K: (TypeExprNode, InClassExprNode | TypeExprNode), V: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[K | V]):
    handles: ClassVar[tuple[Any, ...]]
    key: NodeLike[K]
    value: NodeLike[V]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> DictNode[K, V]: ...

@dataclass(frozen=True)
class ListNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    element: NodeLike[N]
    container_type: ClassVar[type]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> ListNode[N]: ...

@dataclass(frozen=True)
class TupleNode[*Ctx](ContainerNode[Unpack[Ctx]]):
    handles: ClassVar[tuple[Any, ...]]
    items: tuple[BaseNode, ...]
    variable: bool
    def emit(self) -> Any: ...
    @classmethod
    def for_args[N](cls, args: tuple[Any, ...]) -> TupleNode[N]: ...

@dataclass(frozen=True)
class SetNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    element: NodeLike[N]
    container_type: ClassVar[type]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> SetNode[N]: ...

@dataclass(frozen=True)
class FrozenSetNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    element: NodeLike[N]
    container_type: ClassVar[type]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> FrozenSetNode[N]: ...

@dataclass(frozen=True)
class InitVarNode(SpecialFormNode):
    handles: ClassVar[tuple[Any, ...]]
    inner: TypeExprNode
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> InitVarNode: ...

@dataclass(frozen=True)
class SelfNode(InClassExprNode):
    handles: ClassVar[tuple[Any, ...]]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> SelfNode: ...

@dataclass(frozen=True)
class ClassVarNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N], InClassExprNode):
    handles: ClassVar[tuple[Any, ...]]
    inner: NodeLike[N]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> ClassVarNode[N]: ...

@dataclass(frozen=True)
class FinalNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N], SpecialFormNode):
    handles: ClassVar[tuple[Any, ...]]
    inner: NodeLike[N]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> FinalNode[N]: ...

@dataclass(frozen=True)
class RequiredNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N], InClassExprNode):
    handles: ClassVar[tuple[Any, ...]]
    inner: NodeLike[N]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> RequiredNode[N]: ...

@dataclass(frozen=True)
class NotRequiredNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N], InClassExprNode):
    handles: ClassVar[tuple[Any, ...]]
    inner: NodeLike[N]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> NotRequiredNode[N]: ...

@dataclass(frozen=True)
class TypeGuardNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N], SpecialFormNode):
    handles: ClassVar[tuple[Any, ...]]
    target: NodeLike[N]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> TypeGuardNode[N]: ...

@dataclass(frozen=True)
class AnnotatedNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    base: NodeLike[N]
    metadata: list[Any]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> AnnotatedNode[N]: ...

@dataclass(frozen=True)
class ConcatenateNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    parts: list[NodeLike[N]]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> ConcatenateNode[N]: ...

@dataclass(frozen=True)
class CallableNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    args: NodeLike[N] | list[NodeLike[N]] | None
    return_type: NodeLike[N]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> CallableNode[N]: ...

@dataclass(frozen=True)
class UnionNode[*Ctx](ContainerNode[Unpack[Ctx]]):
    handles: ClassVar[tuple[Any, ...]]
    options: tuple[BaseNode, ...]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> UnionNode[Unpack[Ctx]]: ...

@dataclass(frozen=True)
class UnpackNode(SpecialFormNode):
    handles: ClassVar[tuple[Any, ...]]
    target: TupleNode | TypedDictNode | AtomNode | VarNode
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> UnpackNode: ...

def _parse_no_origin_type(typ: Any) -> BaseNode: ...

def _parse_origin_type(origin: Any, args: tuple[Any, ...]) -> BaseNode: ...

def parse_type(typ: Any) -> BaseNode: ...

def parse_type_expr(typ: Any) -> TypeExprNode: ...

def _reject_special(node: BaseNode) -> None: ...

@dataclass
class TypeRenderInfo:
    text: str
    used: set[type]

def _format_node(node: BaseNode) -> TypeRenderInfo: ...

def _format_runtime_type(type_obj: Any) -> TypeRenderInfo: ...

def format_type(type_obj: Any, *, _skip_parse: bool) -> TypeRenderInfo: ...

def format_type_param(tp: Any) -> TypeRenderInfo: ...

def find_typevars(type_obj: Any) -> set[str]: ...

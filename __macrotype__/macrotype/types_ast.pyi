# Generated via: macrotype macrotype -o __macrotype__/macrotype
# Do not edit by hand
from typing import Any, Callable, ClassVar, ParamSpec, TypeVar, TypeVarTuple, Unpack, _TypedDictMeta
from dataclasses import dataclass
from enum import Enum

TypeExpr = Any

class InvalidTypeError(TypeError):
    def __init__(self, message: str, *, hint: str | None, file: str | None, line: int | None) -> None: ...
    def __str__(self) -> str: ...

@dataclass(frozen=True, kw_only=True)
class BaseNode:
    annotations: tuple[Any, ...]
    is_final: bool
    is_required: bool | None
    _registry: ClassVar[dict[Any, type[BaseNode]]]
    handles: ClassVar[tuple[Any, ...]]
    @classmethod
    def __init_subclass__(cls, **kwargs: Any) -> None: ...
    def emit(self) -> Any: ...
    def _apply_modifiers(self, t: Any) -> Any: ...

@dataclass(frozen=True, kw_only=True)
class TypeExprNode(BaseNode): ...

@dataclass(frozen=True, kw_only=True)
class InClassExprNode(BaseNode): ...

@dataclass(frozen=True, kw_only=True)
class SpecialFormNode(BaseNode): ...

@dataclass(frozen=True)
class TypeNode:
    alts: frozenset[BaseNode]
    annotations: tuple[Any, ...]
    is_final: bool
    is_required: bool | None
    def emit(self, *, strict: bool) -> Any: ...
    @staticmethod
    def single(form: BaseNode) -> TypeNode: ...

N = TypeVar('N')

K = TypeVar('K')

V = TypeVar('V')

Ctx = TypeVarTuple('Ctx')

@dataclass(frozen=True, kw_only=True)
class ContainerNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](BaseNode): ...

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
class GenericNode(ContainerNode[TypeExprNode]):
    origin: type[Any]
    args: tuple[BaseNode, ...]
    def emit(self) -> Any: ...

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
    key: TypeNode
    value: TypeNode
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> BaseNode: ...

@dataclass(frozen=True)
class ListNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    element: TypeNode
    container_type: ClassVar[type]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> BaseNode: ...

@dataclass(frozen=True)
class TupleNode[*Ctx](ContainerNode[Unpack[Ctx]]):
    handles: ClassVar[tuple[Any, ...]]
    items: tuple[TypeNode, ...]
    variable: bool
    def emit(self) -> Any: ...
    @classmethod
    def for_args[N](cls, args: tuple[Any, ...]) -> TupleNode[N]: ...

@dataclass(frozen=True)
class SetNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    element: TypeNode
    container_type: ClassVar[type]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> BaseNode: ...

@dataclass(frozen=True)
class FrozenSetNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    element: TypeNode
    container_type: ClassVar[type]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> BaseNode: ...

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
class FinalNode(SpecialFormNode):
    handles: ClassVar[tuple[Any, ...]]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> FinalNode: ...

@dataclass(frozen=True)
class ClassVarNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N], InClassExprNode):
    handles: ClassVar[tuple[Any, ...]]
    inner: NodeLike[N]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> ClassVarNode[N]: ...

@dataclass(frozen=True)
class TypeGuardNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N], SpecialFormNode):
    handles: ClassVar[tuple[Any, ...]]
    target: NodeLike[N]
    def emit(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> TypeGuardNode[N]: ...

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

def _parse_origin_type(origin: Any, args: tuple[Any, ...], raw: Any) -> BaseNode: ...

_on_generic_callback: Callable[[GenericNode], BaseNode] | None

_strict: bool

_eval_globals: dict[str, Any] | None

def parse_type(typ: Any, *, on_generic: Callable[[GenericNode], BaseNode] | None, strict: bool | None, globalns: dict[str, Any] | None) -> BaseNode: ...

def parse_type_expr(typ: Any, *, strict: bool | None, globalns: dict[str, Any] | None) -> TypeExprNode: ...

def _reject_special(node: BaseNode | TypeNode) -> None: ...

@dataclass
class TypeRenderInfo:
    text: str
    used: set[type]

def _format_node(node: BaseNode) -> TypeRenderInfo: ...

def _format_runtime_type(type_obj: Any) -> TypeRenderInfo: ...

def format_type(type_obj: Any, *, globalns: dict[str, Any] | None, _skip_parse: bool) -> TypeRenderInfo: ...

def format_type_param(tp: Any) -> TypeRenderInfo: ...

def find_typevars(type_obj: Any) -> set[str]: ...

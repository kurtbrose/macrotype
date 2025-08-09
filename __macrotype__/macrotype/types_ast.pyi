# Generated via: macrotype macrotype -o __macrotype__/macrotype
# Do not edit by hand
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, ClassVar, ParamSpec, TypeVar, TypeVarTuple, Unpack, _TypedDictMeta

TypeExpr = Any

class InvalidTypeError(TypeError):
    def __init__(self, message: str, *, hint: None | str, file: None | str, line: None | int) -> None: ...
    def __str__(self) -> str: ...

@dataclass(frozen=True, kw_only=True)
class BaseNode:
    annotations: tuple[Any, ...]
    _registry: ClassVar[dict[Any, type[BaseNode]]]
    handles: ClassVar[tuple[Any, ...]]
    @classmethod
    def __init_subclass__(cls, **kwargs: Any) -> None: ...
    def emit(self) -> Any: ...
    def _emit_core(self) -> Any: ...

@dataclass(frozen=True, kw_only=True)
class TypeExprNode(BaseNode): ...

@dataclass(frozen=True, kw_only=True)
class InClassExprNode(BaseNode): ...

@dataclass(frozen=True, kw_only=True)
class SpecialFormNode(BaseNode): ...

@dataclass(frozen=True)
class TypeNode:
    alts: frozenset[BaseNode]
    ann: tuple[Any, ...]
    is_final: bool
    is_required: None | bool
    def emit(self, *, strict: bool) -> Any: ...
    @staticmethod
    def single(form: Any): ...

N = TypeVar("N")

K = TypeVar("K")

V = TypeVar("V")

Ctx = TypeVarTuple("Ctx")

@dataclass(frozen=True, kw_only=True)
class ContainerNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](BaseNode): ...

type NodeLike[N] = ContainerNode[N] | N

@dataclass(frozen=True)
class AtomNode(TypeExprNode):
    type_: Any
    def _emit_core(self) -> Any: ...
    @staticmethod
    def is_atom(type_: Any) -> bool: ...

@dataclass(frozen=True)
class VarNode(TypeExprNode):
    var: ParamSpec | TypeVar | TypeVarTuple
    def _emit_core(self) -> Any: ...

@dataclass(frozen=True)
class TypedDictNode(AtomNode):
    type_: _TypedDictMeta

@dataclass(frozen=True)
class GenericNode(ContainerNode[TypeExprNode]):
    origin: type[Any]
    args: tuple[TypeNode, ...]
    def _emit_core(self) -> Any: ...

@dataclass(frozen=True)
class LiteralNode(TypeExprNode):
    handles: ClassVar[tuple[Any, ...]]
    values: tuple[Enum | None | bool | int | str, ...]
    def _emit_core(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> LiteralNode: ...

@dataclass(frozen=True)
class DictNode[K: (TypeExprNode, InClassExprNode | TypeExprNode), V: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[K | V]):
    handles: ClassVar[tuple[Any, ...]]
    key: TypeNode
    value: TypeNode
    def _emit_core(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> BaseNode: ...

@dataclass(frozen=True)
class ListNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    element: TypeNode
    container_type: ClassVar[type]
    def _emit_core(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> BaseNode: ...

@dataclass(frozen=True)
class TupleNode[*Ctx](ContainerNode[Unpack[Ctx]]):
    handles: ClassVar[tuple[Any, ...]]
    items: tuple[TypeNode, ...]
    variable: bool
    def _emit_core(self) -> Any: ...
    @classmethod
    def for_args[N](cls, args: tuple[Any, ...]) -> TupleNode[N]: ...

@dataclass(frozen=True)
class SetNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    element: TypeNode
    container_type: ClassVar[type]
    def _emit_core(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> BaseNode: ...

@dataclass(frozen=True)
class FrozenSetNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    element: TypeNode
    container_type: ClassVar[type]
    def _emit_core(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> BaseNode: ...

@dataclass(frozen=True)
class InitVarNode(SpecialFormNode):
    handles: ClassVar[tuple[Any, ...]]
    inner: TypeNode
    def _emit_core(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> InitVarNode: ...

@dataclass(frozen=True)
class SelfNode(InClassExprNode):
    handles: ClassVar[tuple[Any, ...]]
    def _emit_core(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> SelfNode: ...

@dataclass(frozen=True)
class ClassVarNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N], InClassExprNode):
    handles: ClassVar[tuple[Any, ...]]
    inner: TypeNode
    def _emit_core(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> ClassVarNode[N]: ...

@dataclass(frozen=True)
class TypeGuardNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N], SpecialFormNode):
    handles: ClassVar[tuple[Any, ...]]
    target: TypeNode
    def _emit_core(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> TypeGuardNode[N]: ...

@dataclass(frozen=True)
class ConcatenateNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    parts: tuple[TypeNode, ...]
    def _emit_core(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> ConcatenateNode[N]: ...

@dataclass(frozen=True)
class CallableNode[N: (TypeExprNode, InClassExprNode | TypeExprNode)](ContainerNode[N]):
    handles: ClassVar[tuple[Any, ...]]
    args: None | TypeNode | tuple[TypeNode, ...]
    return_type: TypeNode
    def _emit_core(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> CallableNode[N]: ...

@dataclass(frozen=True)
class UnpackNode(SpecialFormNode):
    handles: ClassVar[tuple[Any, ...]]
    target: TypeNode
    def _emit_core(self) -> Any: ...
    @classmethod
    def for_args(cls, args: tuple[Any, ...]) -> UnpackNode: ...

def _parse_no_origin_type(typ: Any) -> TypeNode: ...

def _parse_origin_type(origin: Any, args: tuple[Any, ...], raw: Any) -> TypeNode: ...

_on_generic_callback: Callable[[GenericNode], BaseNode] | None

_strict: bool

_eval_globals: None | dict[str, Any]

def parse_type(typ: Any, *, on_generic: Callable[[GenericNode], BaseNode] | None, strict: None | bool, globalns: None | dict[str, Any]) -> TypeNode: ...

def parse_type_expr(typ: Any, *, strict: None | bool, globalns: None | dict[str, Any]) -> TypeNode: ...

def _reject_special(node: BaseNode | TypeNode) -> None: ...

@dataclass
class TypeRenderInfo:
    text: str
    used: set[type]

def _format_node(node: BaseNode | TypeNode) -> TypeRenderInfo: ...

def _format_runtime_type(type_obj: Any) -> TypeRenderInfo: ...

def format_type(type_obj: Any, *, globalns: None | dict[str, Any], _skip_parse: bool) -> TypeRenderInfo: ...

def format_type_param(tp: Any) -> TypeRenderInfo: ...

def find_typevars(type_obj: Any) -> set[str]: ...

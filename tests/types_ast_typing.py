# pyright: strict
from typing import assert_type

from macrotype.types_ast import (
    AtomNode,
    ClassVarNode,
    DictNode,
    InClassExprNode,
    ListNode,
    NodeLike,
    SelfNode,
    TypeExprNode,
    TypeNode,
)

expr_node: NodeLike[TypeExprNode] = AtomNode(int)
expr_node = ListNode[TypeExprNode](TypeNode.single(AtomNode(int)))

class_node: NodeLike[InClassExprNode | TypeExprNode] = ClassVarNode(AtomNode(int))
class_node = SelfNode()

ln: ListNode[TypeExprNode] = ListNode(TypeNode.single(AtomNode(int)))
assert_type(ln.element, TypeNode)

dn: DictNode[TypeExprNode, TypeExprNode] = DictNode(
    TypeNode.single(AtomNode(int)),
    TypeNode.single(AtomNode(str)),
)
assert_type(dn.key, TypeNode)
assert_type(dn.value, TypeNode)

# pyright: strict
from typing import assert_type

from macrotype.types_ast import (
    AtomNode,
    BaseNode,
    ClassVarNode,
    InClassExprNode,
    ListNode,
    NodeLike,
    SelfNode,
    TypeExprNode,
)

expr_node: NodeLike[TypeExprNode] = AtomNode(int)
expr_node = ListNode(frozenset({AtomNode(int)}))

class_node: NodeLike[InClassExprNode | TypeExprNode] = ClassVarNode(AtomNode(int))
class_node = SelfNode()

ln = ListNode(frozenset({AtomNode(int)}))
assert_type(ln.element, frozenset[BaseNode])

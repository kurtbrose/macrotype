# pyright: strict
from typing import assert_type

from macrotype.types_ast import (
    AtomNode,
    ClassVarNode,
    InClassExprNode,
    ListNode,
    NodeLike,
    SelfNode,
    TypeExprNode,
)

expr_node: NodeLike[TypeExprNode] = AtomNode(int)
expr_node = ListNode(AtomNode(int))

class_node: NodeLike[InClassExprNode | TypeExprNode] = ClassVarNode(AtomNode(int))
class_node = SelfNode()

ln = ListNode(AtomNode(int))
assert_type(ln.element, NodeLike[TypeExprNode])

# pyright: strict
from typing import assert_type

from macrotype.types_ast import (
    AtomNode,
    CallableNode,
    ClassVarNode,
    DictNode,
    FrozenSetNode,
    InClassExprNode,
    ListNode,
    NodeLike,
    SelfNode,
    SetNode,
    TupleNode,
    TypeExprNode,
    TypeGuardNode,
    TypeNode,
)

expr_node: NodeLike[TypeExprNode] = AtomNode(int)
expr_node = ListNode[TypeExprNode](TypeNode.single(AtomNode(int)))

class_node: NodeLike[InClassExprNode | TypeExprNode] = ClassVarNode[TypeExprNode](
    TypeNode.single(AtomNode(int))
)
class_node = SelfNode()

ln: ListNode[TypeExprNode] = ListNode(TypeNode.single(AtomNode(int)))
assert_type(ln.element, TypeNode)

dn: DictNode[TypeExprNode, TypeExprNode] = DictNode(
    TypeNode.single(AtomNode(int)),
    TypeNode.single(AtomNode(str)),
)
assert_type(dn.key, TypeNode)
assert_type(dn.value, TypeNode)

sn: SetNode[TypeExprNode] = SetNode(TypeNode.single(AtomNode(int)))
assert_type(sn.element, TypeNode)

fsn: FrozenSetNode[TypeExprNode] = FrozenSetNode(TypeNode.single(AtomNode(str)))
assert_type(fsn.element, TypeNode)

tn: TupleNode[TypeExprNode] = TupleNode((TypeNode.single(AtomNode(int)),), True)
assert_type(tn.items[0], TypeNode)

cn: CallableNode[TypeExprNode] = CallableNode(
    [TypeNode.single(AtomNode(int))],
    TypeNode.single(AtomNode(str)),
)
assert_type(cn.return_type, TypeNode)
if isinstance(cn.args, list):
    assert_type(cn.args[0], TypeNode)

cvn: ClassVarNode[TypeExprNode] = ClassVarNode[TypeExprNode](TypeNode.single(AtomNode(int)))
assert_type(cvn.inner, TypeNode)

tgn: TypeGuardNode[TypeExprNode] = TypeGuardNode[TypeExprNode](TypeNode.single(AtomNode(int)))
assert_type(tgn.target, TypeNode)

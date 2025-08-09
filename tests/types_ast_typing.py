# pyright: strict
from typing import ParamSpec, assert_type

from macrotype.types_ast import (
    AtomNode,
    BaseNode,
    CallableNode,
    ClassVarNode,
    ConcatenateNode,
    DictNode,
    FrozenSetNode,
    GenericNode,
    InClassExprNode,
    InitVarNode,
    ListNode,
    NodeLike,
    SelfNode,
    SetNode,
    TupleNode,
    TypeExprNode,
    TypeGuardNode,
    TypeNode,
    UnpackNode,
    VarNode,
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
    (TypeNode.single(AtomNode(int)),),
    TypeNode.single(AtomNode(str)),
)
assert_type(cn.return_type, TypeNode)
if isinstance(cn.args, tuple):
    assert_type(cn.args[0], TypeNode)

cvn: ClassVarNode[TypeExprNode] = ClassVarNode[TypeExprNode](TypeNode.single(AtomNode(int)))
assert_type(cvn.inner, TypeNode)

ivn: InitVarNode = InitVarNode(TypeNode.single(AtomNode(int)))
assert_type(ivn.inner, TypeNode)

tgn: TypeGuardNode[TypeExprNode] = TypeGuardNode[TypeExprNode](TypeNode.single(AtomNode(int)))
assert_type(tgn.target, TypeNode)

P = ParamSpec("P")

gn: GenericNode = GenericNode(list, (TypeNode.single(AtomNode(int)),))
assert_type(gn.args[0], TypeNode)

un: TypeNode = TypeNode(alts=frozenset({AtomNode(int), AtomNode(str)}))
assert_type(list(un.alts)[0], BaseNode)

ccn: ConcatenateNode[TypeExprNode] = ConcatenateNode(
    (TypeNode.single(AtomNode(int)), TypeNode.single(VarNode(P)))
)
assert_type(ccn.parts[0], TypeNode)

unpn: UnpackNode = UnpackNode(
    TypeNode.single(TupleNode[TypeExprNode]((TypeNode.single(AtomNode(int)),), False))
)
assert_type(unpn.target, TypeNode)

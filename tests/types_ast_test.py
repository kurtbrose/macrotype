import collections
import dataclasses
import enum
import typing

import pytest

from macrotype.types_ast import (
    AtomNode,
    CallableNode,
    ClassVarNode,
    ConcatenateNode,
    DictNode,
    FrozenSetNode,
    GenericNode,
    InitVarNode,
    InvalidTypeError,
    ListNode,
    LiteralNode,
    SelfNode,
    SetNode,
    TupleNode,
    TypedDictNode,
    TypeGuardNode,
    TypeNode,
    UnpackNode,
    VarNode,
    parse_type,
    parse_type_expr,
)


class Color(enum.Enum):
    RED = 1
    BLUE = 2


class TD(typing.TypedDict):
    value: int


T = typing.TypeVar("T")
P = typing.ParamSpec("P")
Ts = typing.TypeVarTuple("Ts")
AliasListT = typing.TypeAliasType("AliasListT", list[T], type_params=(T,))


class Box(typing.Generic[T]):
    pass


PARSINGS = {
    int: TypeNode.single(AtomNode(int)),
    str: TypeNode.single(AtomNode(str)),
    None: TypeNode.single(AtomNode(None)),
    typing.Any: TypeNode.single(AtomNode(typing.Any)),
    typing.Literal[1, "x", True, None]: TypeNode.single(LiteralNode((1, "x", True, None))),
    typing.Literal[Color.RED]: TypeNode.single(LiteralNode((Color.RED,))),
    dict: TypeNode.single(AtomNode(dict)),
    list: TypeNode.single(AtomNode(list)),
    tuple: TypeNode.single(AtomNode(tuple)),
    set: TypeNode.single(AtomNode(set)),
    frozenset: TypeNode.single(AtomNode(frozenset)),
    dict[()]: TypeNode.single(AtomNode(dict)),
    dict[int]: TypeNode.single(GenericNode(dict, (TypeNode.single(AtomNode(int)),))),
    dict[int, str]: TypeNode.single(
        DictNode(
            TypeNode.single(AtomNode(int)),
            TypeNode.single(AtomNode(str)),
        )
    ),
    dict[int, typing.Any]: TypeNode.single(
        DictNode(
            TypeNode.single(AtomNode(int)),
            TypeNode.single(AtomNode(typing.Any)),
        )
    ),
    list[()]: TypeNode.single(AtomNode(list)),
    list[int]: TypeNode.single(ListNode(TypeNode.single(AtomNode(int)))),
    list[list[int]]: TypeNode.single(
        ListNode(TypeNode.single(ListNode(TypeNode.single(AtomNode(int)))))
    ),
    dict[str, list[int]]: TypeNode.single(
        DictNode(
            TypeNode.single(AtomNode(str)),
            TypeNode.single(ListNode(TypeNode.single(AtomNode(int)))),
        )
    ),
    tuple[()]: TypeNode.single(TupleNode((), False)),
    tuple[int]: TypeNode.single(TupleNode((TypeNode.single(AtomNode(int)),), True)),
    tuple[int, str]: TypeNode.single(
        TupleNode(
            (
                TypeNode.single(AtomNode(int)),
                TypeNode.single(AtomNode(str)),
            ),
            False,
        )
    ),
    tuple[int, ...]: TypeNode.single(TupleNode((TypeNode.single(AtomNode(int)),), True)),
    tuple[int, str, ...]: TypeNode.single(
        TupleNode(
            (
                TypeNode.single(AtomNode(int)),
                TypeNode.single(AtomNode(str)),
            ),
            True,
        )
    ),
    tuple[typing.Unpack[Ts]]: TypeNode.single(
        TupleNode(
            (TypeNode.single(UnpackNode(TypeNode.single(VarNode(Ts)))),),
            False,
        )
    ),
    set[int]: TypeNode.single(SetNode(TypeNode.single(AtomNode(int)))),
    frozenset[str]: TypeNode.single(FrozenSetNode(TypeNode.single(AtomNode(str)))),
    typing.Union[int, str]: TypeNode(alts=frozenset({AtomNode(int), AtomNode(str)})),
    int | str: TypeNode(alts=frozenset({AtomNode(int), AtomNode(str)})),
    typing.Union[int, str, None]: TypeNode(
        alts=frozenset({AtomNode(int), AtomNode(str), AtomNode(type(None))})
    ),
    dict[str, typing.Union[int, None]]: TypeNode.single(
        DictNode(
            TypeNode.single(AtomNode(str)),
            TypeNode(alts=frozenset({AtomNode(int), AtomNode(type(None))})),
        )
    ),
    typing.Callable[[int, str], bool]: TypeNode.single(
        CallableNode(
            (TypeNode.single(AtomNode(int)), TypeNode.single(AtomNode(str))),
            TypeNode.single(AtomNode(bool)),
        )
    ),
    typing.Callable[..., int]: TypeNode.single(CallableNode(None, TypeNode.single(AtomNode(int)))),
    typing.Annotated[int, "x"]: TypeNode.single(AtomNode(int, node_ann=("x",))),
    dataclasses.InitVar: TypeNode.single(InitVarNode(TypeNode.single(AtomNode(typing.Any)))),
    dataclasses.InitVar[int]: TypeNode.single(InitVarNode(TypeNode.single(AtomNode(int)))),
    typing.Self: TypeNode.single(SelfNode()),
    typing.Unpack[tuple[int, str]]: TypeNode.single(
        UnpackNode(
            TypeNode.single(
                TupleNode(
                    (
                        TypeNode.single(AtomNode(int)),
                        TypeNode.single(AtomNode(str)),
                    ),
                    False,
                )
            )
        )
    ),
    typing.Unpack[TD]: TypeNode.single(UnpackNode(TypeNode.single(TypedDictNode(TD)))),
    TD: TypeNode.single(TypedDictNode(TD)),
    typing.ClassVar: TypeNode.single(ClassVarNode(TypeNode.single(AtomNode(typing.Any)))),
    typing.ClassVar[int]: TypeNode.single(ClassVarNode(TypeNode.single(AtomNode(int)))),
    typing.Final: TypeNode(is_final=True),
    typing.Final[int]: TypeNode(alts=frozenset({AtomNode(int)}), is_final=True),
    typing.NoReturn: TypeNode.single(AtomNode(typing.NoReturn)),
    typing.Never: TypeNode.single(AtomNode(typing.Never)),
    typing.LiteralString: TypeNode.single(AtomNode(typing.LiteralString)),
    typing.TypeGuard[int]: TypeNode.single(TypeGuardNode(TypeNode.single(AtomNode(int)))),
    typing.NotRequired[int]: TypeNode(alts=frozenset({AtomNode(int)}), is_required=False),
    typing.Required[str]: TypeNode(alts=frozenset({AtomNode(str)}), is_required=True),
    T: TypeNode.single(VarNode(T)),
    P: TypeNode.single(VarNode(P)),
    Ts: TypeNode.single(VarNode(Ts)),
    typing.Unpack[Ts]: TypeNode.single(UnpackNode(TypeNode.single(VarNode(Ts)))),
    AliasListT: TypeNode.single(ListNode(TypeNode.single(VarNode(T)))),
    typing.Concatenate[int, P]: TypeNode.single(
        ConcatenateNode(
            (
                TypeNode.single(AtomNode(int)),
                TypeNode.single(VarNode(P)),
            )
        )
    ),
    typing.Callable[P, int]: TypeNode.single(
        CallableNode(
            TypeNode.single(VarNode(P)),
            TypeNode.single(AtomNode(int)),
        )
    ),
    typing.Callable[typing.Concatenate[int, P], int]: TypeNode.single(
        CallableNode(
            TypeNode.single(
                ConcatenateNode(
                    (
                        TypeNode.single(AtomNode(int)),
                        TypeNode.single(VarNode(P)),
                    )
                )
            ),
            TypeNode.single(AtomNode(int)),
        )
    ),
    typing.Deque[int]: TypeNode.single(
        GenericNode(
            collections.deque,
            (TypeNode.single(AtomNode(int)),),
        )
    ),
    Box[int]: TypeNode.single(GenericNode(Box, (TypeNode.single(AtomNode(int)),))),
}


def test_parsing_roundtrip() -> None:
    actual = {t: parse_type(t) for t in PARSINGS}
    assert actual == PARSINGS


def test_invalid_literal() -> None:
    with pytest.raises(TypeError):
        parse_type(typing.Literal[object()])


def test_unrecognized_type_atom() -> None:
    with pytest.raises(InvalidTypeError):
        parse_type(123)


def test_generic_nodes() -> None:
    assert parse_type(typing.Deque[int]) == TypeNode.single(
        GenericNode(collections.deque, (TypeNode.single(AtomNode(int)),))
    )
    assert parse_type(Box[int]) == TypeNode.single(
        GenericNode(Box, (TypeNode.single(AtomNode(int)),))
    )


def test_invalid_tuple() -> None:
    with pytest.raises(TypeError):
        parse_type(tuple[..., int])
    with pytest.raises(TypeError):
        parse_type(tuple[int, ..., str])


def test_tuple_requires_unpack_typevartuple() -> None:
    with pytest.raises(TypeError):
        parse_type(tuple[Ts])


def test_invalid_unpack() -> None:
    with pytest.raises(TypeError):
        parse_type(typing.Unpack[list[int]])


def test_strict_flag() -> None:
    with pytest.raises(InvalidTypeError):
        parse_type(dict[int], strict=True)
    with pytest.raises(InvalidTypeError):
        parse_type(list, strict=True)
    with pytest.raises(InvalidTypeError):
        parse_type(Box, strict=True)


def test_invalid_initvar() -> None:
    with pytest.raises(TypeError):
        parse_type(dataclasses.InitVar[int, str])


def test_initvar_special_form() -> None:
    with pytest.raises(TypeError):
        parse_type_expr(dataclasses.InitVar[int])


def test_self_in_expr() -> None:
    with pytest.raises(TypeError):
        parse_type_expr(list[typing.Self])


def test_classvar_special_form() -> None:
    with pytest.raises(TypeError):
        parse_type_expr(typing.ClassVar[int])


def test_final_special_form() -> None:
    with pytest.raises(TypeError):
        parse_type_expr(typing.Final[int])
    with pytest.raises(TypeError):
        parse_type_expr(typing.Final)


def test_typeguard_special_form() -> None:
    with pytest.raises(TypeError):
        parse_type_expr(typing.TypeGuard[int])


def test_annotated_nesting() -> None:
    nested = typing.Annotated[typing.Annotated[int, "a"], "b"]
    expected = TypeNode.single(AtomNode(int, node_ann=("a", "b")))
    assert parse_type(nested) == expected
    assert parse_type_expr(nested) == expected


def test_annotated_classvar() -> None:
    ann = typing.Annotated[typing.ClassVar[int], "x"]
    assert parse_type(ann) == TypeNode.single(
        ClassVarNode(TypeNode.single(AtomNode(int)), node_ann=("x",))
    )
    with pytest.raises(TypeError):
        parse_type_expr(ann)


def test_notrequired_special_form() -> None:
    with pytest.raises(TypeError):
        parse_type_expr(typing.NotRequired[int])


def test_required_special_form() -> None:
    with pytest.raises(TypeError):
        parse_type_expr(typing.Required[str])


def test_nested_required_notrequired() -> None:
    with pytest.raises(TypeError):
        parse_type_expr(list[typing.NotRequired[int]])
    with pytest.raises(TypeError):
        parse_type_expr(list[typing.Required[int]])


def test_annotated_requires_metadata() -> None:
    bad = typing._AnnotatedAlias(int, ())
    with pytest.raises(InvalidTypeError):
        parse_type(bad)


def test_concatenate_requires_paramspec() -> None:
    bad = typing._ConcatenateGenericAlias(typing.Concatenate, (int, str))
    with pytest.raises(InvalidTypeError):
        parse_type(bad)

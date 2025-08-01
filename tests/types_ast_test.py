import dataclasses
import enum
import typing

import pytest

from macrotype.types_ast import (
    AnnotatedNode,
    AtomNode,
    CallableNode,
    ClassVarNode,
    ConcatenateNode,
    DictNode,
    FinalNode,
    FrozenSetNode,
    InitVarNode,
    ListNode,
    LiteralNode,
    NotRequiredNode,
    RequiredNode,
    SelfNode,
    SetNode,
    TupleNode,
    TypedDictNode,
    TypeGuardNode,
    UnionNode,
    UnpackNode,
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


PARSINGS = {
    int: AtomNode(int),
    str: AtomNode(str),
    None: AtomNode(None),
    typing.Any: AtomNode(typing.Any),
    typing.Literal[1, "x", True, None]: LiteralNode([1, "x", True, None]),
    typing.Literal[Color.RED]: LiteralNode([Color.RED]),
    dict: DictNode(AtomNode(typing.Any), AtomNode(typing.Any)),
    list: ListNode(AtomNode(typing.Any)),
    tuple: TupleNode([AtomNode(typing.Any)], variable=True),
    set: SetNode(AtomNode(typing.Any)),
    frozenset: FrozenSetNode(AtomNode(typing.Any)),
    dict[()]: DictNode(AtomNode(typing.Any), AtomNode(typing.Any)),
    dict[int, str]: DictNode(AtomNode(int), AtomNode(str)),
    dict[int, typing.Any]: DictNode(AtomNode(int), AtomNode(typing.Any)),
    list[()]: ListNode(AtomNode(typing.Any)),
    list[int]: ListNode(AtomNode(int)),
    list[list[int]]: ListNode(ListNode(AtomNode(int))),
    dict[str, list[int]]: DictNode(AtomNode(str), ListNode(AtomNode(int))),
    tuple[()]: TupleNode([]),
    tuple[int, str]: TupleNode([AtomNode(int), AtomNode(str)]),
    tuple[int, ...]: TupleNode([AtomNode(int)], variable=True),
    tuple[int, str, ...]: TupleNode(
        [AtomNode(int), AtomNode(str)],
        variable=True,
    ),
    set[int]: SetNode(AtomNode(int)),
    frozenset[str]: FrozenSetNode(AtomNode(str)),
    typing.Union[int, str]: UnionNode([AtomNode(int), AtomNode(str)]),
    int | str: UnionNode([AtomNode(int), AtomNode(str)]),
    typing.Union[int, str, None]: UnionNode([AtomNode(int), AtomNode(str), AtomNode(type(None))]),
    dict[str, typing.Union[int, None]]: DictNode(
        AtomNode(str),
        UnionNode([AtomNode(int), AtomNode(type(None))]),
    ),
    typing.Callable[[int, str], bool]: CallableNode([AtomNode(int), AtomNode(str)], AtomNode(bool)),
    typing.Callable[..., int]: CallableNode(None, AtomNode(int)),
    typing.Annotated[int, "x"]: AnnotatedNode(AtomNode(int), ["x"]),
    dataclasses.InitVar: InitVarNode(AtomNode(typing.Any)),
    dataclasses.InitVar[int]: InitVarNode(AtomNode(int)),
    typing.Self: SelfNode(),
    typing.Unpack[tuple[int, str]]: UnpackNode(TupleNode([AtomNode(int), AtomNode(str)])),
    typing.Unpack[TD]: UnpackNode(TypedDictNode(TD)),
    TD: TypedDictNode(TD),
    typing.ClassVar[int]: ClassVarNode(AtomNode(int)),
    typing.Final[int]: FinalNode(AtomNode(int)),
    typing.NoReturn: AtomNode(typing.NoReturn),
    typing.Never: AtomNode(typing.Never),
    typing.LiteralString: AtomNode(typing.LiteralString),
    typing.TypeGuard[int]: TypeGuardNode(AtomNode(int)),
    typing.NotRequired[int]: NotRequiredNode(AtomNode(int)),
    typing.Required[str]: RequiredNode(AtomNode(str)),
    T: AtomNode(T),
    P: AtomNode(P),
    Ts: AtomNode(Ts),
    typing.Unpack[Ts]: UnpackNode(AtomNode(Ts)),
    AliasListT: ListNode(AtomNode(T)),
    typing.Concatenate[int, P]: ConcatenateNode([AtomNode(int), AtomNode(P)]),
    typing.Callable[P, int]: CallableNode(AtomNode(P), AtomNode(int)),
    typing.Callable[typing.Concatenate[int, P], int]: CallableNode(
        ConcatenateNode([AtomNode(int), AtomNode(P)]),
        AtomNode(int),
    ),
}


def test_parsing_roundtrip() -> None:
    actual = {t: parse_type(t) for t in PARSINGS}
    assert actual == PARSINGS


def test_invalid_literal() -> None:
    with pytest.raises(TypeError):
        parse_type(typing.Literal[object()])


def test_unsupported_origin() -> None:
    with pytest.raises(NotImplementedError):
        parse_type(typing.Deque[int])


def test_invalid_tuple() -> None:
    with pytest.raises(TypeError):
        parse_type(tuple[..., int])
    with pytest.raises(TypeError):
        parse_type(tuple[int, ..., str])


def test_invalid_unpack() -> None:
    with pytest.raises(TypeError):
        parse_type(typing.Unpack[list[int]])


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


def test_typeguard_special_form() -> None:
    with pytest.raises(TypeError):
        parse_type_expr(typing.TypeGuard[int])


def test_annotated_nesting() -> None:
    nested = typing.Annotated[typing.Annotated[int, "a"], "b"]
    expected = AnnotatedNode(AtomNode(int), ["a", "b"])
    assert parse_type(nested) == expected
    assert parse_type_expr(nested) == expected


def test_annotated_classvar() -> None:
    ann = typing.Annotated[typing.ClassVar[int], "x"]
    assert parse_type(ann) == AnnotatedNode(ClassVarNode(AtomNode(int)), ["x"])
    with pytest.raises(TypeError):
        parse_type_expr(ann)


def test_notrequired_special_form() -> None:
    with pytest.raises(TypeError):
        parse_type_expr(typing.NotRequired[int])


def test_required_special_form() -> None:
    with pytest.raises(TypeError):
        parse_type_expr(typing.Required[str])

import enum
import typing

import pytest

from macrotype.types_ast import (
    AnnotatedNode,
    AtomNode,
    CallableNode,
    DictNode,
    FrozenSetNode,
    ListNode,
    LiteralNode,
    SetNode,
    TupleNode,
    TypedDictNode,
    UnionNode,
    UnpackNode,
    parse_type,
)


class Color(enum.Enum):
    RED = 1
    BLUE = 2


class TD(typing.TypedDict):
    value: int


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
    typing.Union[int, str, None]: UnionNode([AtomNode(int), AtomNode(str), AtomNode(type(None))]),
    dict[str, typing.Union[int, None]]: DictNode(
        AtomNode(str),
        UnionNode([AtomNode(int), AtomNode(type(None))]),
    ),
    typing.Callable[[int, str], bool]: CallableNode([AtomNode(int), AtomNode(str)], AtomNode(bool)),
    typing.Callable[..., int]: CallableNode(None, AtomNode(int)),
    typing.Annotated[int, "x"]: AnnotatedNode(AtomNode(int), ["x"]),
    typing.Unpack[tuple[int, str]]: UnpackNode(TupleNode([AtomNode(int), AtomNode(str)])),
    typing.Unpack[TD]: UnpackNode(TypedDictNode(TD)),
    TD: TypedDictNode(TD),
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

from typing import TypeVarTuple, Unpack, Tuple, Generic, TypedDict, Any

Ts = TypeVarTuple("Ts")


def as_tuple(*args: Unpack[Ts]) -> Tuple[Unpack[Ts]]:
    return tuple(args)


class Variadic(Generic[*Ts]):
    def __init__(self, *args: Unpack[Ts]) -> None:
        self.args = tuple(args)

    def to_tuple(self) -> Tuple[Unpack[Ts]]:
        return self.args


class Info(TypedDict):
    name: str
    age: int


def with_kwargs(**kwargs: Unpack[Info]) -> Info:
    return kwargs


def sum_of(*args: tuple[int]) -> int:
    return sum(args)


def dict_echo(**kwargs: dict[str, Any]) -> dict[str, Any]:
    return kwargs

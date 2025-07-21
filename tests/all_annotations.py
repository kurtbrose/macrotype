import re
from typing import (
    Optional,
    Union,
    Callable,
    TypeVar,
    Generic,
    Literal,
    Annotated,
    TypedDict,
    ParamSpec,
    NewType,
    overload,
)

T = TypeVar("T")
P = ParamSpec("P")
UserId = NewType("UserId", int)

class AllAnnotations:
    a: list[str]
    b: dict[str, int]
    c: Optional[int]
    d: Union[int, str]
    e: int | str
    f: Callable[[int, str], bool]
    g: Annotated[int, "meta"]
    h: re.Pattern[str]
    uid: UserId
    def copy(self, param: T) -> T: ...
    def curry(self, f: Callable[P, int]) -> Callable[P, int]: ...

    class Nested:
        x: float
        y: str

class ChildClass(AllAnnotations):
    ...

class SampleDict(TypedDict):
    name: str
    age: int

class PartialDict(TypedDict, total=False):
    id: int
    hint: str


class Slotted:
    __slots__ = ("x", "y")
    x: int
    y: str


@overload
def over(x: int) -> int: ...


@overload
def over(x: str) -> str: ...


def over(x: int | str) -> int | str:
    return x

from typing import Callable, Literal, NewType, overload
from re import Pattern

UserId = NewType('UserId', int)

class AllAnnotations:
    a: list[str]
    b: dict[str, int]
    c: int | None
    d: int | str
    e: int | str
    f: Callable[[int, str], bool]
    g: int
    h: Pattern[str]
    uid: UserId
    lit_attr: Literal['a', 'b']
    def copy[T](param: T) -> T: ...
    def curry[P](f: Callable[P, int]) -> Callable[P, int]: ...
    def literal_method(flag: Literal['on', 'off']) -> Literal[1, 0]: ...
    class Nested:
        x: float
        y: str

class ChildClass(AllAnnotations):
    pass

class SampleDict(TypedDict):
    name: str
    age: int

class PartialDict(TypedDict, total=False):
    id: int
    hint: str

class Slotted:
    x: int
    y: str

@overload
def over(x: int) -> int: ...

@overload
def over(x: str) -> str: ...

def over(x: int | str) -> int | str: ...

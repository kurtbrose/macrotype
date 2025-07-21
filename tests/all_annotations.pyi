from typing import Callable, NewType
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
    def copy[T](param: T) -> T: ...
    def curry[P](f: Callable[P, int]) -> Callable[P, int]: ...
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

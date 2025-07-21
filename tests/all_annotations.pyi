from typing import Callable, Union
from re import Pattern
from types import UnionType

class AllAnnotations:
    a: list[str]
    b: dict[str, int]
    c: Union[int, None]
    d: Union[int, str]
    e: UnionType[int, str]
    f: Callable[[int, str], bool]
    g: int
    h: Pattern[str]
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

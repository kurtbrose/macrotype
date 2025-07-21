from typing import Callable, Generic, Literal, NewType, overload
from functools import cached_property
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
    def copy[T](self, param: T) -> T: ...
    def curry[P](self, f: Callable[P, int]) -> Callable[P, int]: ...
    def literal_method(self, flag: Literal['on', 'off']) -> Literal[1, 0]: ...
    @classmethod
    def cls_method(cls, value: int) -> AllAnnotations: ...
    @staticmethod
    def static_method(value: int) -> int: ...
    @property
    def prop(self) -> int: ...
    @cached_property
    def cached(self) -> int: ...
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

class GenericClass(Generic[T]):
    value: T
    def get[T](self) -> T: ...

class Slotted:
    x: int
    y: str

def make_wrapped(t: type): ...

class Wrapper:
    value: int

class Wrapper:
    value: Pattern[str]

@overload
def over(x: int) -> int: ...

@overload
def over(x: str) -> str: ...

def over(x: int | str) -> int | str: ...

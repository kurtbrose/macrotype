# Generated via: manual separation of unsupported features
# These declarations use syntax from PEP 695 that mypy fails to parse.
from typing import Callable, ClassVar, TypeAliasType, TypeVar, TypeVarTuple, ParamSpec, Unpack, NewType, Tuple, final, overload, Concatenate
from dataclasses import dataclass, InitVar
from macrotype.meta_types import make_literal_map

T = TypeVar('T')
P = ParamSpec('P')
Ts = TypeVarTuple('Ts')
U = TypeVar('U')
NumberLike = TypeVar('NumberLike')
UserId = NewType('UserId', int)

MyList = list[int]

type StrList = list[str]

type Alias0[T] = list[T]

type Alias1[T] = Alias0[T]

type AliasNewType = UserId

type AliasTypeVar[T] = T

type AliasUnion = int | str

type ListOrSet[T] = list[T] | set[T]

type IntFunc[**P] = Callable[P, int]

type LabeledTuple[*Ts] = tuple[str, Unpack[Ts]]

type RecursiveList[T] = T | list[RecursiveList[T]]

AliasListT = TypeAliasType('AliasListT', list[T], type_params=(T,))
AliasFuncP = TypeAliasType('AliasFuncP', Callable[P, int], type_params=(P,))
AliasTupleTs = TypeAliasType('AliasTupleTs', tuple[Unpack[Ts]], type_params=(Ts,))
AliasNumberLikeList = TypeAliasType('AliasNumberLikeList', list[NumberLike], type_params=(NumberLike,))
AliasBoundU = TypeAliasType('AliasBoundU', list[U], type_params=(U,))

class NewGeneric[T]:
    value: T
    def get(self) -> T: ...

class BoundClass[T: int]:
    value: T

class ConstrainedClass[T: (int, str)]:
    value: T

def as_tuple[*Ts](*args: Unpack[Ts]) -> tuple[Unpack[Ts]]: ...

class Variadic[*Ts]:
    def __init__(self, *args: Unpack[Ts]) -> None: ...
    def to_tuple(self) -> tuple[Unpack[Ts]]: ...

def prepend_one[**P](fn: Callable[Concatenate[int, P], int]) -> Callable[P, int]: ...

@dataclass
class InitVarExample:
    x: int
    init_only: InitVar[int]
    def __post_init__(self, init_only: int) -> None: ...

@overload
def loop_over(x: bytes) -> str: ...

@overload
def loop_over(x: bytearray) -> str: ...

def loop_over(x: bytes | bytearray) -> str: ...

EmittedMap = make_literal_map("EmittedMap", {"a": 1, "b": 2})

def use_params(*args: P.args, **kwargs: P.kwargs) -> int: ...

InferredT = TypeVar('InferredT', infer_variance=True)

@final
def final_func(x: int) -> int: ...

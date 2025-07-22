from typing import TypeVar, Generic

T = TypeVar('T')

class OldGeneric(Generic[T]):
    value: T
    def get(self) -> T:
        return self.value

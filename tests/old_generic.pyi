from typing import TypeVar

T = TypeVar('T')

class OldGeneric[T]:
    value: T
    def get(self) -> T: ...

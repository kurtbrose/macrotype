from typing import TypeVar

T = TypeVar('T')

class NewGeneric[T]:
    value: T
    def get(self) -> T:
        return self.value

from dataclasses import dataclass
from typing import ClassVar

@dataclass
class Example:
    x: int
    y: ClassVar[int] = 0

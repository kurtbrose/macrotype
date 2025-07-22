from typing import ClassVar
from dataclasses import dataclass

@dataclass
class Example:
    x: int
    y: ClassVar[int]

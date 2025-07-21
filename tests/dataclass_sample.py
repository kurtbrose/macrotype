from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

@dataclass(frozen=True, slots=True)
class Frozen:
    a: int
    b: int

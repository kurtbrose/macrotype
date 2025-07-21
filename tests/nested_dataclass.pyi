from dataclasses import dataclass

@dataclass
class Outer:
    x: int
    @dataclass
    class Inner:
        y: int

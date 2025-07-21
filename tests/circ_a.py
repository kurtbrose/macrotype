from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.circ_b import B
else:
    B = int

class A:
    pass

def takes_b(x: 'B') -> None:
    pass

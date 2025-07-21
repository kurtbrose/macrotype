from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.circ_a import A
else:
    A = int

class B:
    pass

def takes_a(x: 'A') -> None:
    pass

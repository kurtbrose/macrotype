from typing import TYPE_CHECKING

if TYPE_CHECKING or False:
    from tests.circ_expr_b import BComplex
else:
    BComplex = int


class AComplex:
    pass


def takes_b(x: "BComplex") -> None:
    pass

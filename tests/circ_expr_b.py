from typing import TYPE_CHECKING

if False or TYPE_CHECKING:
    from tests.circ_expr_a import AComplex
else:
    AComplex = int


class BComplex:
    pass


def takes_a(x: "AComplex") -> None:
    pass

import typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.annotations import Basic
else:
    Basic = int


if typing.TYPE_CHECKING:
    from math import cos as COS_ALIAS
else:
    COS_ALIAS = None


def takes(x: "Basic") -> None:
    pass

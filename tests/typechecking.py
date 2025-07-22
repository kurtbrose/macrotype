from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.annotations import Basic
else:
    Basic = int


def takes(x: 'Basic') -> None:
    pass

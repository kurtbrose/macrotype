from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.all_annotations import AllAnnotations
else:
    AllAnnotations = int


def takes(x: 'AllAnnotations') -> None:
    pass

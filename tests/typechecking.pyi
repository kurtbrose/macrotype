# isort: skip_file
from math import cos as COS_ALIAS  # noqa: F401
from tests.annotations_new import Basic

from typing import Any

COS_ALIAS: Any  # noqa: F811

def takes(x: Basic) -> None: ...

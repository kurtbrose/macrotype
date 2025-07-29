# These annotations use syntax standardized in PEP 695 but unsupported by mypy.
# Only ``TypeVar.infer_variance`` is currently unimplemented.
from typing import TypeVar

# ``TypeVar`` with the ``infer_variance`` parameter from PEP 695 is not yet
# implemented by mypy.
InferredT = TypeVar("InferredT", infer_variance=True)

# Generated via: manual separation of unsupported features
# These declarations use syntax from PEP 695 that mypy fails to parse.
from typing import TypeVar

InferredT = TypeVar("InferredT", infer_variance=True)

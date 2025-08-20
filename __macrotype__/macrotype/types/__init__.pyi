# Generated via: macrotype macrotype/types/__init__.py -o __macrotype__/macrotype/types/__init__.pyi
# Do not edit by hand
from __future__ import annotations

from macrotype.types.ir import Ty

def from_type(obj: object, ctx: str) -> Ty: ...
def normalize_annotation(obj: object, ctx: str) -> object: ...

# Generated via: macrotype macrotype/modules/transformers/dataclass_transform.py --strict -o __macrotype__/macrotype/modules/transformers/dataclass_transform.pyi
# Do not edit by hand
from __future__ import _Feature
from macrotype.modules.ir import ModuleDecl

from typing import Any

annotations = _Feature

def has_transform(cls: type) -> bool: ...

def _dt_decorator(obj: Any) -> None | str: ...

def apply_dataclass_transform(mi: ModuleDecl) -> None: ...

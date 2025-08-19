# Generated via: macrotype macrotype/modules/transformers/dataclass.py --strict -o __macrotype__/macrotype/modules/transformers/dataclass.pyi
# Do not edit by hand
from __future__ import _Feature
from dataclasses import _DataclassParams
from macrotype.modules.ir import ClassDecl, ModuleDecl

from typing import Any

annotations = _Feature

_DATACLASS_DEFAULTS: dict[str, Any]

def _dataclass_auto_methods(params: None | _DataclassParams) -> set[str]: ...

def _dataclass_decorator(klass: type) -> None | str: ...

def _transform_class(sym: ClassDecl, cls: type) -> None: ...

def transform_dataclasses(mi: ModuleDecl) -> None: ...

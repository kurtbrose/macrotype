# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations

from dataclasses import _DataclassParams
from typing import Any

from macrotype.modules.ir import ClassDecl, ModuleDecl

annotations = annotations

_DATACLASS_DEFAULTS: dict[str, Any]

def _dataclass_auto_methods(params: None | _DataclassParams) -> set[str]: ...
def _dataclass_decorator(klass: type) -> None | str: ...
def _transform_class(sym: ClassDecl, cls: type) -> None: ...
def transform_dataclasses(mi: ModuleDecl) -> None: ...

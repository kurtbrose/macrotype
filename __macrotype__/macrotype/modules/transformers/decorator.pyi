# Generated via: macrotype macrotype/modules/transformers/decorator.py -o __macrotype__/macrotype/modules/transformers/decorator.pyi
# Do not edit by hand
from macrotype.modules.ir import ModuleDecl
from typing import Any, Callable

def _unwrap_decorated_function(obj: Any) -> Callable[..., Any] | None: ...

def unwrap_decorated_functions(mi: ModuleDecl) -> None: ...

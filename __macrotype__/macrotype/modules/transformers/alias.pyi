# Generated via: macrotype macrotype/modules/transformers/alias.py -o __macrotype__/macrotype/modules/transformers/alias.pyi --strict
# Do not edit by hand
from __future__ import annotations

from macrotype.modules.ir import Decl, ModuleDecl

annotations = annotations

def _transform_alias_vars(decls: list[Decl]) -> list[Decl]: ...
def synthesize_aliases(mi: ModuleDecl) -> None: ...

# Generated via: macrotype macrotype
# Do not edit by hand
from __future__ import annotations
from macrotype.types.ir import Ty
from macrotype.types.normalize import norm
from macrotype.types.parse import parse
from macrotype.types.resolve import ResolveEnv, resolve
from macrotype.types.unparse import unparse, unparse_top
from macrotype.types.validate import validate

def from_type(obj: object, ctx: str) -> Ty: ...

def normalize_annotation(obj: object, ctx: str) -> object: ...

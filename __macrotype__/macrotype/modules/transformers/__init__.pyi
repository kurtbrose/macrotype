# Generated via: macrotype macrotype/modules/transformers/__init__.py -o __macrotype__/macrotype/modules/transformers/__init__.pyi
# Do not edit by hand
from .add_comment import add_comments
from .alias import synthesize_aliases
from .dataclass import transform_dataclasses
from .decorator import unwrap_decorated_functions
from .descriptor import normalize_descriptors
from .enum import transform_enums
from .flag import normalize_flags
from .foreign_symbol import canonicalize_foreign_symbols
from .namedtuple import transform_namedtuples
from .newtype import transform_newtypes
from .overload import expand_overloads
from .param_default import infer_param_defaults
from .protocol import prune_protocol_methods
from .typeddict import prune_inherited_typeddict_fields
from .generic import transform_generics

__all__ = [
    "add_comments",
    "synthesize_aliases",
    "transform_dataclasses",
    "normalize_descriptors",
    "transform_enums",
    "normalize_flags",
    "canonicalize_foreign_symbols",
    "expand_overloads",
    "transform_newtypes",
    "infer_param_defaults",
    "prune_protocol_methods",
    "prune_inherited_typeddict_fields",
    "transform_namedtuples",
    "transform_generics",
    "unwrap_decorated_functions",
]

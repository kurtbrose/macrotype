from .add_comment import add_comments
from .alias import synthesize_aliases
from .constant import infer_constant_types
from .dataclass import transform_dataclasses
from .dataclass_transform import apply_dataclass_transform
from .decorator import unwrap_decorated_functions
from .descriptor import normalize_descriptors
from .duplicate import canonicalize_local_aliases
from .enum import transform_enums
from .flag import normalize_flags
from .foreign_symbol import canonicalize_foreign_symbols
from .generic import transform_generics
from .namedtuple import transform_namedtuples
from .newtype import transform_newtypes
from .overload import expand_overloads
from .param_default import infer_param_defaults
from .protocol import prune_protocol_methods
from .resolve_imports import resolve_imports
from .source_info import add_source_info
from .typeddict import prune_inherited_typeddict_fields

__all__ = [
    "add_comments",
    "add_source_info",
    "synthesize_aliases",
    "infer_constant_types",
    "transform_dataclasses",
    "apply_dataclass_transform",
    "normalize_descriptors",
    "transform_enums",
    "normalize_flags",
    "canonicalize_foreign_symbols",
    "canonicalize_local_aliases",
    "expand_overloads",
    "transform_newtypes",
    "infer_param_defaults",
    "prune_protocol_methods",
    "prune_inherited_typeddict_fields",
    "transform_namedtuples",
    "transform_generics",
    "unwrap_decorated_functions",
    "resolve_imports",
]

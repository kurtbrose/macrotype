from .add_comment import add_comments
from .alias import synthesize_aliases
from .dataclass import transform_dataclasses
from .descriptor import normalize_descriptors
from .flag import normalize_flags
from .foreign_symbol import canonicalize_foreign_symbols
from .overload import expand_overloads
from .typeddict import prune_inherited_typeddict_fields

__all__ = [
    "add_comments",
    "synthesize_aliases",
    "transform_dataclasses",
    "normalize_descriptors",
    "normalize_flags",
    "canonicalize_foreign_symbols",
    "expand_overloads",
    "prune_inherited_typeddict_fields",
]

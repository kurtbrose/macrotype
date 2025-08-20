from __future__ import annotations

"""Module analysis pipeline."""

from types import ModuleType

from .emit import emit_module
from .ir import ModuleDecl, SourceInfo
from .scanner import scan_module

__all__ = [
    "ModuleDecl",
    "add_source_info",
    "add_comments",
    "from_module",
    "expand_overloads",
    "normalize_flags",
    "normalize_descriptors",
    "canonicalize_foreign_symbols",
    "recover_custom_generics",
    "canonicalize_local_aliases",
    "unwrap_decorated_functions",
    "infer_param_defaults",
    "transform_newtypes",
    "transform_enums",
    "transform_namedtuples",
    "transform_generics",
    "synthesize_aliases",
    "prune_inherited_typeddict_fields",
    "prune_protocol_methods",
    "emit_module",
    "scan_module",
    "transform_dataclasses",
    "resolve_imports",
]


def __getattr__(name: str):
    if name in {
        "add_source_info",
        "add_comments",
        "canonicalize_foreign_symbols",
        "recover_custom_generics",
        "canonicalize_local_aliases",
        "unwrap_decorated_functions",
        "infer_param_defaults",
        "transform_newtypes",
        "transform_enums",
        "transform_namedtuples",
        "transform_generics",
        "expand_overloads",
        "normalize_descriptors",
        "normalize_flags",
        "prune_inherited_typeddict_fields",
        "prune_protocol_methods",
        "synthesize_aliases",
        "transform_dataclasses",
        "resolve_imports",
    }:
        from . import transformers as _t

        return getattr(_t, name)
    raise AttributeError(name)


def from_module(
    mod: ModuleType,
    *,
    source_info: SourceInfo | None = None,
    strict: bool = False,
) -> ModuleDecl:
    """Scan *mod* into a :class:`ModuleDecl` and attach comments.

    If *strict* is ``True``, all annotations are normalized and validated via
    ``macrotype.types`` before returning.
    """

    from . import transformers as _t

    mi = scan_module(mod)
    _t.add_source_info(mi, source_info)
    _t.canonicalize_foreign_symbols(mi)
    _t.recover_custom_generics(mi)
    _t.unwrap_decorated_functions(mi)
    _t.canonicalize_local_aliases(mi)
    _t.synthesize_aliases(mi)
    _t.transform_newtypes(mi)
    _t.transform_enums(mi)
    _t.transform_generics(mi)
    _t.transform_dataclasses(mi)
    _t.apply_dataclass_transform(mi)
    _t.infer_constant_types(mi)
    _t.prune_inherited_typeddict_fields(mi)
    _t.normalize_descriptors(mi)
    _t.transform_namedtuples(mi)
    _t.infer_param_defaults(mi)
    _t.normalize_flags(mi)
    _t.prune_protocol_methods(mi)
    _t.expand_overloads(mi)
    _t.recover_custom_generics(mi)
    _t.add_comments(mi)
    _t.resolve_imports(mi)

    if strict:
        from macrotype.types import normalize_annotation

        from .ir import AnnExpr

        for decl in mi.iter_all_decls():
            for site in decl.get_annotation_sites():
                if site.role != "alias_value":
                    ctx = "call_params" if site.role == "param" else "top"
                    ann = site.annotation
                    if isinstance(ann, AnnExpr):
                        norm = normalize_annotation(ann.evaluated, ctx=ctx)
                        site.annotation = AnnExpr(expr=ann.expr, evaluated=norm)
                    else:
                        site.annotation = normalize_annotation(ann, ctx=ctx)

    return mi

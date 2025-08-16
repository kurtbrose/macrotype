from importlib import import_module

from macrotype.modules import emit_module, from_module


def test_emit_annotations_new_strict() -> None:
    ann = import_module("tests.annotations_new")
    mi = from_module(ann, strict=True)
    lines = emit_module(mi)
    assert (
        "def with_paramspec_args_kwargs[**P](fn: Callable[P, int], *args: P.args, **kwargs: P.kwargs) -> int: ..."
        in lines
    )
    assert (
        "def prepend_one[**P](fn: Callable[Concatenate[int, P], int]) -> Callable[P, int]: ..."
        in lines
    )

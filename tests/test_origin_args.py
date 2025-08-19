from macrotype.modules.emit import _origin_and_args
from macrotype.types.parse import _origin_args


class TypeTrap:
    def __getattr__(self, name: str) -> None:
        if name == "type":
            raise AssertionError("unexpected 'type' access")
        raise AttributeError(name)


def test_emit_origin_and_args_ignores_dynamic_attrs() -> None:
    assert _origin_and_args(TypeTrap()) == (None, ())


def test_parse_origin_args_ignores_dynamic_attrs() -> None:
    assert _origin_args(TypeTrap()) == (None, ())

# Coding and Testing Standards

This project focuses on generating `.pyi` files from live modules. The library and
tests rely heavily on features available in Python 3.13. Earlier Python versions
are not guaranteed to work or pass the test suite.

## Style
- Use four spaces for indentation and prefer double quotes for strings.
- Keep helper structures simple, often implemented with `@dataclass`.
- Public APIs are re-exported through `__all__`.

## Testing
- Run `pytest` from the repository root to execute the test suite.
- The suite generates stub files and compares them against expected `.pyi` files.
- `tests/test_mypy.py` runs `mypy` on most `.pyi` files in `tests/` to ensure
the generated stubs are valid. Make sure `mypy` is installed.
- Modules loaded with `load_module_from_path(..., type_checking=True)` execute
`if TYPE_CHECKING:` blocks to capture additional annotations. This is required
for tests dealing with circular imports and dynamic annotations.

## Notes
- Because tests rely on Python 3.13 features, running them on earlier versions
may fail.

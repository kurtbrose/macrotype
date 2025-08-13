from __future__ import annotations

from pathlib import Path

DEFAULT_OUT_DIR = Path("__macrotype__")


def _default_output_path(path: Path, cwd: Path, *, is_file: bool) -> Path:
    """Return the default output location for ``path`` relative to ``cwd``."""

    abs_path = path if path.is_absolute() else cwd / path
    if not abs_path.is_relative_to(cwd):
        raise ValueError(f"{path} is not under {cwd}; specify -o")
    rel = abs_path.relative_to(cwd)
    base = DEFAULT_OUT_DIR / rel
    return base.with_suffix(".pyi") if is_file else base


def main(argv: list[str] | None = None) -> int:
    from .__main__ import main as _main

    return _main(argv)


def check_main(argv: list[str] | None = None) -> int:
    from .typecheck import main as _main

    return _main(argv)


__all__ = ["main", "check_main", "DEFAULT_OUT_DIR", "_default_output_path"]

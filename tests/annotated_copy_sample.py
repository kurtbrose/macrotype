from __future__ import annotations

from typing import Iterable


def quoted_param(value: "int") -> "str":
    return str(value)


class QuotedBox:
    value: "int"

    def wrap(self, items: "Iterable[int]") -> "list[int]":
        return list(items)

from __future__ import annotations

import sys
from typing import Generic, NewType, TypeVar

T = TypeVar("T")


class Mapped(Generic[T]):
    """Placeholder for ``sqlalchemy.orm.Mapped``."""


class Base:
    def __init_subclass__(cls) -> None:  # noqa: D401 - simple demo
        typename = f"{cls.__name__}Id"
        new_type = NewType(typename, int)
        cls.id_type = new_type
        cls.__annotations__["id"] = Mapped[new_type]
        cls.__annotations__["id_type"] = type[new_type]
        mod = sys.modules[cls.__module__]
        setattr(mod, typename, new_type)


class Manager(Base): ...


class Employee(Base):
    manager_id: Mapped[Manager.id_type]

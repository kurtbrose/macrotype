# Generated via: macrotype demos/sqla_demos.py -o demos/sqla_demos.pyi
# Do not edit by hand
from typing import NewType, TypeVar

T = TypeVar("T")

class Mapped[T]:
    pass

class Base:
    @classmethod
    def __init_subclass__(cls) -> None: ...

ManagerId = NewType("ManagerId", int)

class Manager(Base):
    id: Mapped[ManagerId]
    id_type: type[ManagerId]

EmployeeId = NewType("EmployeeId", int)

class Employee(Base):
    manager_id: Mapped[ManagerId]
    id: Mapped[EmployeeId]
    id_type: type[EmployeeId]

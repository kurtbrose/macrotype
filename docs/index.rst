.. include:: ../README.rst

Generic type handling
---------------------

``macrotype`` can parse generic classes that lack built‑in handlers.  In this
case :func:`macrotype.types_ast.parse_type` produces a ``TypeNode`` containing a
``GenericNode`` capturing the original class and its type arguments.  Libraries
can customize the result by providing an ``on_generic`` callback::

    from collections import deque
    from typing import Deque
    from macrotype.types_ast import GenericNode, ListNode, parse_type

    def handle(node: GenericNode):
        if node.origin is deque:
            return ListNode(node.args[0])
        return node

    parse_type(Deque[int], on_generic=handle)

Dynamic annotations
-------------------

``all_annotations`` collects ``__annotations__`` from a class and its bases.
With a comprehension you can derive new annotations using standard Python::

    from typing import Final
    from macrotype.meta_types import all_annotations

    class Cls:
        a: int
        b: str | None

    class FinalCls:
        __annotations__ = {k: Final[v] for k, v in all_annotations(Cls).items()}

    class OptionalCls:
        __annotations__ = {k: v | None for k, v in all_annotations(Cls).items()}

    class OmittedCls:
        __annotations__ = {k: v for k, v in all_annotations(Cls).items() if k != "b"}

    class ReplacedCls:
        __annotations__ = {**all_annotations(Cls), "a": str}


Module Documentation
--------------------

.. automodule:: macrotype
    :members:

.. toctree::
   :maxdepth: 1

   demos


.. include:: ../README.rst

Generic type handling
---------------------

``macrotype`` can parse generic classes that lack built‑in handlers.  In this
case :func:`macrotype.types_ast.parse_type` produces a
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

Module Documentation
--------------------

.. automodule:: macrotype
    :members:

.. toctree::
   :maxdepth: 1

   demos


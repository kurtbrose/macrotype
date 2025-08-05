Metaprogramming demos
=====================

``macrotype`` can capture types that are generated dynamically.  The example
below creates a new ``NewType`` for each subclass using ``__init_subclass__``.
This pattern is similar to how SQLAlchemy models can define typed primary keys.

.. literalinclude:: ../demos/sqla_demos.py
   :language: python

Running ``macrotype`` generates the following stub:

.. literalinclude:: ../demos/sqla_demos.pyi
   :language: python

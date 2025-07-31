Macrotype
=========

Consider this:

.. code-block:: python

    VAL = 42

    def get() -> type(VAL):
        return VAL

This is perfectly valid Python, but type checkers don't accept it.  Instead,
you are supposed to write out all type references statically or use very
limited global aliases.

``macrotype`` makes this work exactly as you expect with all static type
checkers, so your types can be as dynamic as the rest of your Python code.

How?
-----

``macrotype`` is a CLI tool intended to be run before static type checking:

.. code-block:: python

    macrotype your_module

``macrotype`` imports your modules under normal Python and then generates
corresponding ``.pyi`` files with all types pinned statically so the type
checker can understand them.

In our example, ``macrotype`` would generate this:

.. code-block:: python

    VAL: int

    def get() -> int: ...

``macrotype`` is the bridge between static type checkers and your dynamic
code.  ``macrotype`` will import your modules as Python and then re-export the
runtime types back out into a form that static type checkers can consume.

What else?
----------

In addition to the CLI tool, there are also helpers for generating dynamic
types.  See ``macrotype.meta_types``.  These are intended for you to import to
enable dynamic programming patterns which would be unthinkable without
``macrotype``.

Type checking
-------------

Most users will want to run their static type checker through the
``macrotype.check`` entrypoint.  This wrapper generates stub files and then
invokes your checker with ``PYTHONPATH`` configured so the generated stubs are
found.  The console script is installed as ``macrotype-check`` and accepts the
checker command followed by the paths to stub.  Any additional arguments after
``--`` are passed through to the checker:

.. code-block:: python

    macrotype-check mypy src/ -- --strict

Stubs are written to ``__macrotype__`` by default; use ``-o`` to choose a
different directory.

Dogfooding
----------

The ``macrotype`` project uses the CLI on itself.  Running:

.. code-block:: python

    python -m macrotype macrotype

regenerates the stub files for the package in place.  A CI job ensures that the
checked in ``.pyi`` files are always in sync with this command.

Documentation
-------------

Full documentation is available on `Read the Docs <https://macrotype.readthedocs.io/>`_.
To build the documentation locally, install the project with the ``doc`` optional dependency:

.. code-block:: python

    pip install .[doc]
    sphinx-build docs docs/_build

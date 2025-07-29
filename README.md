# Macrotype

Consider this:

```python
VAL = 42

def get() -> type(VAL):
    return VAL
```

This is perfectly valid python, but type checkers don't accept it.
Instead, you are supposed to write out all type references statically,
or use very limited global aliases.

`macrotype` makes this work exactly as you expect, with all static
type checkers.  So your types can be as dynamic as the rest of your
python code.

# How?

`macrotype` is a CLI tool intended to be run before static type checking:

```bash
macrotype your_module
```

`macrotype` imports your modules under normal python,
and then generates corresponding `.pyi` files with
all types pinned statically so the type checker can understand them.

In our example, `macrotype` would generate this:

```python
VAL: int

def get() -> int: ...
```

`macrotype` is the bridge between static type checkers
and your dynamic code.  `macrotype` will import your modules as
python, and then re-export the runtime types back out into a form
that static type checkers can consume.

# What else?

In addition to the CLI tool, there are also helpers for generating
dynamic types.  See `macrotype.meta_types`.  These are intended
for you to import to enable dynamic programming patterns which
would be unthinkable without `macrotype`.

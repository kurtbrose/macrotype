"""Module with invalid annotation to test strict mode error handling."""

# Ellipsis must be final in tuple annotations; this intentionally violates that rule.
STRICT_BAD_TUPLE: tuple[..., int]

from __future__ import annotations


class ValueObject:
    """Base class for immutable value objects compared *by value*."""

    __slots__ = ()

    # pylint: disable=compare-to-zero
    def __eq__(self, other):  # type: ignore[override]  # noqa: D401 (simple verb)
        return self.__dict__ == getattr(other, "__dict__", {})

    def __hash__(self):  # noqa: D401 (simple verb)
        return hash(tuple(sorted(self.__dict__.items())))

from __future__ import annotations

from typing import Generic, TypeVar, Union
from typing_extensions import final

T = TypeVar("T")
E = TypeVar("E")


class Result(Generic[T, E]):
    """Rust‑style Result — avoids exceptions by making success & failure explicit."""

    __slots__ = ("_is_ok", "_value")

    _is_ok: bool
    _value: Union[T, E]

    def __init__(self, is_ok: bool, value: Union[T, E]):
        self._is_ok = is_ok
        self._value = value

    # ------------------------------------------------------ public API
    def is_ok(self) -> bool:  # noqa: D401 (simple verb)
        return self._is_ok

    def is_err(self) -> bool:  # noqa: D401 (simple verb)
        return not self._is_ok

    def ok(self) -> T | None:
        if self._is_ok:
            return self._value  # type: ignore[return-value]
        return None

    def err(self) -> E | None:
        if not self._is_ok:
            return self._value  # type: ignore[return-value]
        return None

    # ------------------------------------------------------ helpers
    def map(self, fn):  # noqa: ANN001
        return Ok(fn(self.ok())) if self.is_ok() else self  # type: ignore[arg-type]

    def unwrap_or(self, default: T) -> T:  # noqa: D401 (simple verb)
        if self.is_ok():
            return self._value  # type: ignore[return-value]
        return default


@final
class Ok(Result[T, E]):
    __slots__ = ()

    def __init__(self, value: T):
        super().__init__(True, value)


@final
class Err(Result[T, E]):
    __slots__ = ()

    def __init__(self, error: E):
        super().__init__(False, error)

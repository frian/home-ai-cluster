"""Process-local cardinality for HAC-owned adapter invocation intervals."""

import asyncio


class ExecutionIntervalCardinality:
    """Track active local adapter invocations for one composed HAC process."""

    def __init__(self, limit: int = 1) -> None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("Execution interval limit must be a positive integer")
        self._limit = limit
        self._value = 0
        self._lock = asyncio.Lock()

    @property
    def value(self) -> int:
        """Return the current number of HAC-owned invocation intervals."""
        return self._value

    async def enter(self) -> None:
        """Record entry to one local adapter invocation interval."""
        async with self._lock:
            self._value += 1

    async def try_enter(self) -> bool:
        """Enter one interval only when it remains within the fixed limit."""
        async with self._lock:
            if self._value >= self._limit:
                return False
            self._value += 1
            return True

    async def exit(self) -> None:
        """Record exit from one local adapter invocation interval."""
        async with self._lock:
            if self._value <= 0:
                raise RuntimeError("Execution interval cardinality cannot be negative")
            self._value -= 1

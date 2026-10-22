"""Client-side token budget, so a per-minute provider limit is respected instead of hit.

Retrying after a 429 works, but it wastes requests and, on trial keys, the whole minute. When
the limit is known, waiting before sending is cheaper and predictable.
"""

import threading
import time
from collections import deque
from collections.abc import Callable

WINDOW_S = 60.0


def estimate_tokens(text: str) -> int:
    """Text averages about 4 characters per token; counting 3 errs high, never over the limit."""
    return max(1, len(text) // 3)


class TokenBudget:
    """Sliding one-minute window: ``acquire`` blocks until ``tokens`` fit under the limit."""

    def __init__(
        self,
        tokens_per_minute: int,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if tokens_per_minute <= 0:
            raise ValueError("tokens_per_minute must be positive")
        self.limit = tokens_per_minute
        self._clock = clock
        self._sleep = sleep
        self._spent: deque[tuple[float, int]] = deque()
        self._lock = threading.Lock()

    def _used(self, now: float) -> int:
        while self._spent and now - self._spent[0][0] >= WINDOW_S:
            self._spent.popleft()
        return sum(tokens for _, tokens in self._spent)

    def acquire(self, tokens: int) -> float:
        """Reserve ``tokens``; returns how long it waited. A request above the limit waits for
        an empty window and then goes alone."""
        waited = 0.0
        with self._lock:
            while True:
                now = self._clock()
                used = self._used(now)
                if not self._spent or used + tokens <= self.limit:
                    self._spent.append((now, tokens))
                    return waited
                delay = WINDOW_S - (now - self._spent[0][0])
                self._sleep(delay)
                waited += delay

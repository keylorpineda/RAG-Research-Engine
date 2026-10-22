"""Limits for a public demo running on a provider quota (all off by default).

- A daily question cap, counted from the ``queries`` table so it survives restarts and sleeps.
- A per-client hourly limit, so one visitor cannot spend the whole day's cap.
- A small answer cache: repeated questions (the suggested ones, mostly) cost no provider calls
  and do not count. Only for instances whose documents do not change, since entries are not
  invalidated when they do.
"""

import functools
import threading
import time
from collections import OrderedDict, deque
from collections.abc import Callable, Hashable

from fastapi import Request
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError
from app.models.models import QueryLog

HOUR = 3600.0
MAX_TRACKED_CLIENTS = 10_000


class DailyLimitError(AppError):
    status_code = 429
    code = "daily_limit_reached"


class ClientLimitError(AppError):
    status_code = 429
    code = "too_many_requests"


class SlidingWindowLimiter:
    """At most ``limit`` events per key within ``window`` seconds. Thread-safe, in memory."""

    def __init__(
        self, limit: int, window: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.limit = limit
        self.window = window
        self._clock = clock
        self._events: dict[Hashable, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: Hashable) -> bool:
        now = self._clock()
        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= now - self.window:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            # Forget idle clients so the map does not grow with every visitor.
            if len(self._events) > MAX_TRACKED_CLIENTS:
                cutoff = now - self.window
                self._events = {k: v for k, v in self._events.items() if v[-1] > cutoff}
            return True


class TtlCache[K: Hashable, V]:
    """Least recently used entries are dropped past ``size``; entries expire after ``ttl``."""

    def __init__(self, size: int, ttl: float, clock: Callable[[], float] = time.monotonic) -> None:
        self.size = size
        self.ttl = ttl
        self._clock = clock
        self._items: OrderedDict[K, tuple[float, V]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: K) -> V | None:
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            stored, value = item
            if self._clock() - stored > self.ttl:
                del self._items[key]
                return None
            self._items.move_to_end(key)
            return value

    def put(self, key: K, value: V) -> None:
        if self.size <= 0:
            return
        with self._lock:
            self._items[key] = (self._clock(), value)
            self._items.move_to_end(key)
            while len(self._items) > self.size:
                self._items.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


def questions_today(db: Session) -> int:
    """Questions answered or refused since midnight in the database's time zone."""
    today = text("date_trunc('day', NOW())")
    return db.scalar(select(func.count()).select_from(QueryLog).where(QueryLog.ts >= today)) or 0


def questions_left_today(db: Session) -> int | None:
    if settings.daily_question_limit is None:
        return None
    return max(0, settings.daily_question_limit - questions_today(db))


def client_key(request: Request) -> str:
    """The visitor's address. Behind a proxy (Vercel, Render) it is the first forwarded hop."""
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "")
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else "unknown"


@functools.cache
def _limiter_for(limit: int) -> SlidingWindowLimiter:
    return SlidingWindowLimiter(limit, HOUR)


def _limiter() -> SlidingWindowLimiter | None:
    limit = settings.questions_per_client_per_hour
    return None if limit is None else _limiter_for(limit)


def check_question_allowed(db: Session, request: Request) -> None:
    """Raise if the demo's daily cap or this client's hourly share is spent."""
    if questions_left_today(db) == 0:
        raise DailyLimitError(
            "The demo has used today's questions. It resets at midnight UTC: come back tomorrow."
        )
    limiter = _limiter()
    if limiter is not None and not limiter.allow(client_key(request)):
        raise ClientLimitError(
            f"You have asked {limiter.limit} questions in the last hour. Try again later."
        )

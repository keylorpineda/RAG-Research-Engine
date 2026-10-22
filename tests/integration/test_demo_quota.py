from datetime import timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import demo_limits
from app.core.config import settings
from app.models.models import QueryLog


def test_the_daily_count_only_includes_today(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    yesterday = db.scalar(select(func.now())) - timedelta(days=1)  # type: ignore[operator]
    db.add_all([QueryLog(query_text="old", ts=yesterday), QueryLog(query_text="a")])
    db.add(QueryLog(query_text="b"))
    db.commit()

    assert demo_limits.questions_today(db) == 2

    monkeypatch.setattr(settings, "daily_question_limit", 3)
    assert demo_limits.questions_left_today(db) == 1
    monkeypatch.setattr(settings, "daily_question_limit", None)
    assert demo_limits.questions_left_today(db) is None

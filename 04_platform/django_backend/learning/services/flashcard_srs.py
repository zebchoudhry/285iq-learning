"""
SM-2-style scheduling for flashcard reviews.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Tuple

RATING_TO_QUALITY = {
    "again": 1,
    "hard": 2,
    "good": 4,
    "easy": 5,
}


def sm2_step(
    quality: int,
    ease_factor: float,
    interval_days: int,
    repetition_count: int,
) -> Tuple[float, int, int]:
    """Return (new_ease, new_interval_days, new_repetition_count)."""
    q = max(0, min(5, quality))
    if q < 3:
        new_reps = 0
        new_interval = 1
    else:
        if repetition_count == 0:
            new_interval = 1
        elif repetition_count == 1:
            new_interval = 6
        else:
            new_interval = max(1, round(interval_days * ease_factor))
        new_reps = repetition_count + 1

    new_ef = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ef = max(1.3, float(new_ef))
    return new_ef, new_interval, new_reps


def next_due_date(interval_days: int, from_day: date | None = None) -> date:
    base = from_day or date.today()
    return base + timedelta(days=max(1, interval_days))

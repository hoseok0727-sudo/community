from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from app.models import Post


def _ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def post_engagement_score(post: Post) -> float:
    return (0.05 * max(post.view_count, 0)) + (2.0 * max(post.upvote_count, 0)) + (
        1.5 * max(post.comment_count, 0)
    )


def recency_weight(published_at: datetime, now: datetime, half_life_hours: int = 12) -> float:
    published_at = _ensure_aware_utc(published_at)
    now = _ensure_aware_utc(now)
    age_hours = max((now - published_at).total_seconds() / 3600, 0)
    if half_life_hours <= 0:
        return 1.0
    return 0.5 ** (age_hours / half_life_hours)


def compute_topic_score(
    posts: list[Post],
    window_hours: int,
    now: datetime | None = None,
) -> tuple[float, str]:
    if not posts:
        return 0.0, "stable"
    now = now or datetime.now(timezone.utc)
    now = _ensure_aware_utc(now)
    window_hours = max(window_hours, 1)

    engagement = sum(post_engagement_score(post) for post in posts) / len(posts)
    engagement_norm = min(math.log1p(engagement) / 6.0, 1.0)

    recency = sum(recency_weight(post.published_at, now) for post in posts) / len(posts)

    split = now - timedelta(hours=window_hours / 2)
    recent_count = sum(1 for p in posts if _ensure_aware_utc(p.published_at) >= split)
    older_count = max(len(posts) - recent_count, 1)
    velocity_ratio = recent_count / older_count
    velocity_norm = min(velocity_ratio, 3.0) / 3.0

    score = (0.35 * engagement_norm) + (0.40 * recency) + (0.25 * velocity_norm)
    trend = "up" if velocity_ratio > 1.3 else "down" if velocity_ratio < 0.75 else "stable"
    return round(score, 4), trend

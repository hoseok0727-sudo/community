from datetime import datetime, timedelta, timezone

from app.models import Post
from app.services.scoring import compute_topic_score, recency_weight


def make_post(hours_ago: int, ups: int = 0, comments: int = 0, views: int = 0, now=None) -> Post:
    now = now or datetime.now(timezone.utc)
    return Post(
        gallery_id=1,
        external_id=f"id-{hours_ago}-{ups}",
        url="https://example.com",
        title="sample",
        content="sample",
        author="u",
        published_at=now - timedelta(hours=hours_ago),
        view_count=views,
        upvote_count=ups,
        comment_count=comments,
        raw_metadata={},
    )


def test_recency_weight_decreases(now_utc):
    recent = recency_weight(now_utc - timedelta(hours=1), now_utc)
    old = recency_weight(now_utc - timedelta(hours=24), now_utc)
    assert recent > old


def test_compute_topic_score_trend_up(now_utc):
    posts = [
        make_post(1, ups=10, comments=5, now=now_utc),
        make_post(2, ups=8, comments=4, now=now_utc),
        make_post(3, ups=6, comments=3, now=now_utc),
        make_post(20, ups=1, comments=0, now=now_utc),
    ]
    score, trend = compute_topic_score(posts, window_hours=24, now=now_utc)
    assert 0 <= score <= 1
    assert trend == "up"

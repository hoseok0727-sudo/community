from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Post, Topic, TopicPost, TopicRun
from app.schemas import BriefingOut, TopicOut, TopicPostOut
from app.services.briefing import build_briefing

router = APIRouter(tags=["topics"])


def _latest_run_id(db: Session, window_hours: int | None) -> int | None:
    stmt: Select = select(TopicRun.id).order_by(desc(TopicRun.created_at))
    if window_hours is not None:
        stmt = stmt.where(TopicRun.window_hours == window_hours)
    return db.execute(stmt.limit(1)).scalar_one_or_none()


@router.get("/topics", response_model=list[TopicOut])
def list_topics(
    gallery_id: int | None = Query(default=None),
    window_hours: int | None = Query(default=None, ge=1, le=168),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[Topic]:
    run_id = _latest_run_id(db, window_hours=window_hours)
    if run_id is None:
        return []

    stmt = select(Topic).where(Topic.run_id == run_id).order_by(Topic.score.desc()).limit(limit)
    if gallery_id is not None:
        stmt = stmt.where(Topic.gallery_id == gallery_id)
    return db.execute(stmt).scalars().all()


@router.get("/topic/{topic_id}/posts", response_model=list[TopicPostOut])
def list_topic_posts(topic_id: int, db: Session = Depends(get_db)) -> list[TopicPostOut]:
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    rows = db.execute(
        select(TopicPost, Post)
        .join(Post, Post.id == TopicPost.post_id)
        .where(TopicPost.topic_id == topic_id)
        .order_by(TopicPost.rank.asc())
    ).all()

    result: list[TopicPostOut] = []
    for topic_post, post in rows:
        result.append(
            TopicPostOut(
                post_id=post.id,
                external_id=post.external_id,
                title=post.title,
                url=post.url,
                published_at=post.published_at,
                view_count=post.view_count,
                upvote_count=post.upvote_count,
                comment_count=post.comment_count,
                rank=topic_post.rank,
            )
        )
    return result


@router.get("/briefing", response_model=BriefingOut)
def selected_board_briefing(
    gallery_ids: list[int] = Query(default=[]),
    window_hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=20, ge=1, le=100),
    per_gallery_cap: int = Query(default=120, ge=10, le=500),
    db: Session = Depends(get_db),
) -> BriefingOut:
    return build_briefing(
        db=db,
        gallery_ids=gallery_ids,
        window_hours=window_hours,
        limit=limit,
        per_gallery_cap=per_gallery_cap,
    )


@router.get("/topics/trend")
def topic_trend(
    gallery_id: int,
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
) -> list[dict]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=hours)
    posts = db.execute(
        select(Post)
        .where(Post.gallery_id == gallery_id, Post.published_at >= start)
        .order_by(Post.published_at.asc())
    ).scalars()

    buckets: dict[str, int] = defaultdict(int)
    for post in posts:
        bucket = post.published_at.replace(minute=0, second=0, microsecond=0).isoformat()
        buckets[bucket] += 1
    return [{"bucket": bucket, "count": count} for bucket, count in sorted(buckets.items())]

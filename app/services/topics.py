from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Gallery, Post, Topic, TopicPost, TopicRun
from app.services.topic_engine import build_topic_candidates


def rebuild_topics(
    db: Session,
    window_hours: int,
    gallery_id: int | None = None,
    clear_existing_for_window: bool = False,
) -> TopicRun:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=max(window_hours, 1))

    run = TopicRun(window_hours=window_hours, created_at=now)
    db.add(run)
    db.flush()

    if gallery_id is not None:
        galleries = db.execute(select(Gallery).where(Gallery.id == gallery_id)).scalars().all()
    else:
        galleries = db.execute(select(Gallery).where(Gallery.enabled.is_(True))).scalars().all()

    for gallery in galleries:
        if clear_existing_for_window:
            old_topic_ids = db.execute(
                select(Topic.id).where(
                    Topic.gallery_id == gallery.id,
                    Topic.run.has(TopicRun.window_hours == window_hours),
                )
            ).scalars()
            old_ids = list(old_topic_ids)
            if old_ids:
                db.execute(delete(TopicPost).where(TopicPost.topic_id.in_(old_ids)))
                db.execute(delete(Topic).where(Topic.id.in_(old_ids)))

        posts = db.execute(
            select(Post)
            .where(Post.gallery_id == gallery.id, Post.published_at >= window_start)
            .order_by(Post.published_at.desc())
        ).scalars()
        post_list = list(posts)
        candidates = build_topic_candidates(post_list, window_hours=window_hours)
        for candidate in candidates[:20]:
            topic = Topic(
                gallery_id=gallery.id,
                run_id=run.id,
                title=candidate.title[:255],
                summary=candidate.summary,
                score=candidate.score,
                confidence=candidate.confidence,
                trend=candidate.trend,
                keywords=candidate.keywords,
                created_at=now,
            )
            db.add(topic)
            db.flush()

            for rank, post in enumerate(candidate.posts[:5], start=1):
                db.add(TopicPost(topic_id=topic.id, post_id=post.id, rank=rank))

    db.commit()
    db.refresh(run)
    return run


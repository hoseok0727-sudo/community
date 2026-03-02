from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Gallery, Post
from app.schemas import BriefingGalleryOut, BriefingOut, BriefingPostOut, BriefingTopicOut
from app.services.topic_engine import build_topic_candidates


@dataclass(slots=True)
class _GalleryContext:
    ids: list[int]
    by_id: dict[int, Gallery]


def _resolve_galleries(db: Session, gallery_ids: list[int]) -> _GalleryContext:
    if gallery_ids:
        galleries = db.execute(
            select(Gallery).where(Gallery.id.in_(gallery_ids), Gallery.enabled.is_(True))
        ).scalars().all()
    else:
        galleries = db.execute(select(Gallery).where(Gallery.enabled.is_(True))).scalars().all()

    ids = [gallery.id for gallery in galleries]
    by_id = {gallery.id: gallery for gallery in galleries}
    return _GalleryContext(ids=ids, by_id=by_id)


def build_briefing(
    db: Session,
    gallery_ids: list[int],
    window_hours: int,
    limit: int,
    per_gallery_cap: int,
) -> BriefingOut:
    context = _resolve_galleries(db=db, gallery_ids=gallery_ids)
    if not context.ids:
        return BriefingOut(
            window_hours=window_hours,
            selected_galleries=[],
            topic_count=0,
            topics=[],
        )

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=max(window_hours, 1))

    posts: list[Post] = []
    for gid in context.ids:
        gallery_posts = db.execute(
            select(Post)
            .where(Post.gallery_id == gid, Post.published_at >= window_start)
            .order_by(Post.published_at.desc())
            .limit(max(per_gallery_cap, 1))
        ).scalars().all()
        posts.extend(gallery_posts)

    candidates = build_topic_candidates(posts=posts, window_hours=window_hours)
    selected_galleries = [
        BriefingGalleryOut(id=gallery.id, display_name=gallery.display_name)
        for gallery in context.by_id.values()
    ]

    topics: list[BriefingTopicOut] = []
    for rank, candidate in enumerate(candidates[: max(limit, 1)], start=1):
        involved_ids = sorted({post.gallery_id for post in candidate.posts})
        involved_names = [
            context.by_id[gid].display_name for gid in involved_ids if gid in context.by_id
        ]
        evidence_posts = []
        for post in candidate.posts[:5]:
            gallery_name = context.by_id[post.gallery_id].display_name
            evidence_posts.append(
                BriefingPostOut(
                    post_id=post.id,
                    gallery_id=post.gallery_id,
                    gallery_name=gallery_name,
                    title=post.title,
                    url=post.url,
                    published_at=post.published_at,
                    view_count=post.view_count,
                    upvote_count=post.upvote_count,
                    comment_count=post.comment_count,
                )
            )

        topics.append(
            BriefingTopicOut(
                rank=rank,
                title=candidate.title,
                summary=candidate.summary,
                score=candidate.score,
                confidence=candidate.confidence,
                trend=candidate.trend,
                keywords=candidate.keywords,
                gallery_ids=involved_ids,
                gallery_names=involved_names,
                posts=evidence_posts,
            )
        )

    return BriefingOut(
        window_hours=window_hours,
        selected_galleries=selected_galleries,
        topic_count=len(topics),
        topics=topics,
    )


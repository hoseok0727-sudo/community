from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.registry import CollectorRegistry
from app.models import Gallery, Post

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestResult:
    gallery_id: int
    fetched_count: int
    inserted_count: int
    updated_count: int


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def collect_gallery_posts(
    db: Session,
    gallery: Gallery,
    registry: CollectorRegistry,
    limit: int,
    max_retries: int = 3,
) -> IngestResult:
    collector = registry.get(gallery.source_type)
    fetched = []
    for attempt in range(max_retries):
        try:
            fetched = collector.fetch_posts(gallery.source_key, limit=limit)
            break
        except Exception:
            logger.exception(
                "Collector failed source_type=%s source_key=%s attempt=%d",
                gallery.source_type,
                gallery.source_key,
                attempt + 1,
            )
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
            else:
                return IngestResult(
                    gallery_id=gallery.id,
                    fetched_count=0,
                    inserted_count=0,
                    updated_count=0,
                )

    if not fetched:
        return IngestResult(
            gallery_id=gallery.id,
            fetched_count=0,
            inserted_count=0,
            updated_count=0,
        )

    external_ids = [post.external_id for post in fetched]
    existing = db.execute(
        select(Post).where(Post.gallery_id == gallery.id, Post.external_id.in_(external_ids))
    ).scalars()
    existing_by_external = {post.external_id: post for post in existing}

    inserted_count = 0
    updated_count = 0
    for raw_post in fetched:
        if not raw_post.title:
            continue
        existing_post = existing_by_external.get(raw_post.external_id)
        if existing_post:
            existing_post.url = raw_post.url
            existing_post.title = raw_post.title[:500]
            existing_post.content = raw_post.content
            existing_post.author = raw_post.author[:255]
            existing_post.published_at = _normalize_datetime(raw_post.published_at)
            existing_post.fetched_at = datetime.now(timezone.utc)
            existing_post.view_count = raw_post.view_count
            existing_post.upvote_count = raw_post.upvote_count
            existing_post.comment_count = raw_post.comment_count
            existing_post.raw_metadata = raw_post.raw_metadata
            updated_count += 1
            continue

        new_post = Post(
            gallery_id=gallery.id,
            external_id=raw_post.external_id,
            url=raw_post.url[:1000],
            title=raw_post.title[:500],
            content=raw_post.content,
            author=raw_post.author[:255],
            published_at=_normalize_datetime(raw_post.published_at),
            fetched_at=datetime.now(timezone.utc),
            view_count=raw_post.view_count,
            upvote_count=raw_post.upvote_count,
            comment_count=raw_post.comment_count,
            raw_metadata=raw_post.raw_metadata,
        )
        db.add(new_post)
        inserted_count += 1

    db.commit()
    return IngestResult(
        gallery_id=gallery.id,
        fetched_count=len(fetched),
        inserted_count=inserted_count,
        updated_count=updated_count,
    )


def collect_enabled_galleries(
    db: Session,
    registry: CollectorRegistry,
    limit: int,
) -> list[IngestResult]:
    galleries = db.execute(select(Gallery).where(Gallery.enabled.is_(True))).scalars().all()
    results: list[IngestResult] = []
    for gallery in galleries:
        result = collect_gallery_posts(db=db, gallery=gallery, registry=registry, limit=limit)
        results.append(result)
    return results

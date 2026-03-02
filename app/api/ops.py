from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_admin_guard
from app.collectors.registry import CollectorRegistry
from app.core.config import get_settings
from app.db import get_db
from app.models import Gallery
from app.schemas import CollectRunResult
from app.services.ingest import collect_enabled_galleries, collect_gallery_posts
from app.services.topics import rebuild_topics

router = APIRouter(prefix="/ops", tags=["ops"])
settings = get_settings()
registry = CollectorRegistry()


@router.post(
    "/collect",
    response_model=list[CollectRunResult],
    dependencies=[Depends(get_admin_guard)],
)
def run_collect(
    gallery_id: int | None = Query(default=None),
    limit: int | None = Query(default=None, ge=10, le=500),
    db: Session = Depends(get_db),
) -> list[CollectRunResult]:
    fetch_limit = limit or settings.default_fetch_limit
    if gallery_id is None:
        results = collect_enabled_galleries(db=db, registry=registry, limit=fetch_limit)
        return [CollectRunResult(**result.__dict__) for result in results]

    gallery = db.get(Gallery, gallery_id)
    if gallery is None:
        raise HTTPException(status_code=404, detail="Gallery not found")
    result = collect_gallery_posts(db=db, gallery=gallery, registry=registry, limit=fetch_limit)
    return [CollectRunResult(**result.__dict__)]


@router.post("/topics/rebuild", dependencies=[Depends(get_admin_guard)])
def run_topic_rebuild(
    window_hours: int = Query(default=settings.topic_window_hours, ge=1, le=168),
    gallery_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    run = rebuild_topics(db=db, window_hours=window_hours, gallery_id=gallery_id)
    gallery_count = db.execute(
        select(func.count()).select_from(Gallery).where(Gallery.enabled.is_(True))
    ).scalar_one()
    return {
        "run_id": run.id,
        "window_hours": run.window_hours,
        "created_at": run.created_at.isoformat(),
        "gallery_count": gallery_count,
    }

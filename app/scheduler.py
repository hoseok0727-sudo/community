from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.collectors.registry import CollectorRegistry
from app.core.config import get_settings
from app.db import SessionLocal
from app.services.ingest import collect_enabled_galleries
from app.services.topics import rebuild_topics

logger = logging.getLogger(__name__)
settings = get_settings()
registry = CollectorRegistry()


def _scheduled_pipeline() -> None:
    db = SessionLocal()
    try:
        collect_results = collect_enabled_galleries(
            db=db, registry=registry, limit=settings.default_fetch_limit
        )
        rebuild_topics(db=db, window_hours=settings.topic_window_hours)
        logger.info("Scheduled pipeline complete galleries=%d", len(collect_results))
    except Exception:
        logger.exception("Scheduled pipeline failed")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _scheduled_pipeline,
        trigger="interval",
        minutes=settings.collect_interval_minutes,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120,
    )
    scheduler.start()
    logger.info("Scheduler started interval=%dmin", settings.collect_interval_minutes)
    return scheduler


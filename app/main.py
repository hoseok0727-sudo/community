from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import galleries, ops, topics
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db import init_db
from app.scheduler import start_scheduler

settings = get_settings()
setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    scheduler = None
    if settings.env.lower() != "test":
        scheduler = start_scheduler()
    try:
        yield
    finally:
        if scheduler:
            scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(galleries.router)
app.include_router(topics.router)
app.include_router(ops.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


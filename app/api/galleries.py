from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.collectors.registry import CollectorRegistry
from app.db import get_db
from app.models import Gallery
from app.schemas import GalleryCreate, GalleryOut

router = APIRouter(prefix="/galleries", tags=["galleries"])
registry = CollectorRegistry()


@router.get("", response_model=list[GalleryOut])
def list_galleries(db: Session = Depends(get_db)) -> list[Gallery]:
    return db.execute(select(Gallery).order_by(Gallery.created_at.desc())).scalars().all()


@router.get("/sources", response_model=list[str])
def list_sources() -> list[str]:
    return registry.supported_sources()


@router.post("", response_model=GalleryOut, status_code=status.HTTP_201_CREATED)
def create_gallery(payload: GalleryCreate, db: Session = Depends(get_db)) -> Gallery:
    if payload.source_type not in registry.supported_sources():
        raise HTTPException(status_code=400, detail="Unsupported source_type")
    gallery = Gallery(
        source_type=payload.source_type,
        source_key=payload.source_key.strip(),
        display_name=payload.display_name.strip(),
        enabled=payload.enabled,
    )
    db.add(gallery)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Gallery already exists") from None
    db.refresh(gallery)
    return gallery


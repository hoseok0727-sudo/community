from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GalleryCreate(BaseModel):
    source_type: Literal["dcinside", "reddit", "hackernews"]
    source_key: str = Field(min_length=1, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    enabled: bool = True


class GalleryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_type: str
    source_key: str
    display_name: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gallery_id: int
    title: str
    summary: str
    score: float
    confidence: float
    trend: str
    keywords: list[str]
    created_at: datetime


class TopicPostOut(BaseModel):
    post_id: int
    external_id: str
    title: str
    url: str
    published_at: datetime
    view_count: int
    upvote_count: int
    comment_count: int
    rank: int


class CollectRunResult(BaseModel):
    gallery_id: int
    inserted_count: int
    updated_count: int
    fetched_count: int

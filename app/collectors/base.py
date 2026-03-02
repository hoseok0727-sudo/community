from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


@dataclass(slots=True)
class RawPost:
    external_id: str
    url: str
    title: str
    content: str
    author: str
    published_at: datetime
    view_count: int = 0
    upvote_count: int = 0
    comment_count: int = 0
    raw_metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.published_at.tzinfo is None:
            self.published_at = self.published_at.replace(tzinfo=timezone.utc)


class Collector(Protocol):
    source_type: str

    def fetch_posts(self, source_key: str, limit: int = 100) -> list[RawPost]:
        ...


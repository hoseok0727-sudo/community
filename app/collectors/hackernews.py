from __future__ import annotations

from datetime import datetime, timezone

import httpx
from dateutil.parser import isoparse

from app.collectors.base import RawPost
from app.collectors.utils import safe_int
from app.core.config import get_settings


class HackerNewsCollector:
    source_type = "hackernews"

    def __init__(self) -> None:
        settings = get_settings()
        self.timeout = settings.http_timeout_seconds

    def fetch_posts(self, source_key: str, limit: int = 100) -> list[RawPost]:
        size = min(max(limit, 10), 1000)
        query = source_key.strip()
        params = {"tags": "story", "hitsPerPage": size}
        if query:
            params["query"] = query

        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            response = client.get("https://hn.algolia.com/api/v1/search_by_date", params=params)
            response.raise_for_status()
            payload = response.json()

        hits = payload.get("hits", [])
        posts: list[RawPost] = []
        for hit in hits:
            object_id = str(hit.get("objectID") or "").strip()
            if not object_id:
                continue

            published_raw = hit.get("created_at")
            try:
                published_at = isoparse(published_raw).astimezone(timezone.utc)
            except Exception:
                published_at = datetime.now(timezone.utc)

            hn_url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
            title = (hit.get("title") or hit.get("story_title") or "").strip()
            content = (hit.get("comment_text") or "").strip()
            posts.append(
                RawPost(
                    external_id=object_id,
                    url=hn_url,
                    title=title,
                    content=content,
                    author=(hit.get("author") or "").strip(),
                    published_at=published_at,
                    view_count=0,
                    upvote_count=safe_int(hit.get("points")),
                    comment_count=safe_int(hit.get("num_comments")),
                    raw_metadata={"source": "hackernews", "query": query},
                )
            )
        return posts


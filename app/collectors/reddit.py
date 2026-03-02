from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.collectors.base import RawPost
from app.collectors.utils import safe_int
from app.core.config import get_settings


class RedditCollector:
    source_type = "reddit"

    def __init__(self) -> None:
        settings = get_settings()
        self.timeout = settings.http_timeout_seconds
        self.headers = {"User-Agent": "community-briefing/0.1 (+https://github.com/hoseok0727-sudo/community)"}

    def fetch_posts(self, source_key: str, limit: int = 100) -> list[RawPost]:
        size = min(max(limit, 10), 100)
        url = f"https://www.reddit.com/r/{source_key}/new.json"
        params = {"limit": size, "raw_json": 1}

        with httpx.Client(
            timeout=self.timeout,
            headers=self.headers,
            follow_redirects=True,
        ) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

        items = payload.get("data", {}).get("children", [])
        posts: list[RawPost] = []
        for item in items:
            data = item.get("data", {})
            external_id = data.get("id")
            if not external_id:
                continue
            permalink = data.get("permalink", "")
            post_url = f"https://www.reddit.com{permalink}" if permalink else data.get("url", "")
            published_at = datetime.fromtimestamp(data.get("created_utc", 0), tz=timezone.utc)
            posts.append(
                RawPost(
                    external_id=external_id,
                    url=post_url,
                    title=(data.get("title") or "").strip(),
                    content=(data.get("selftext") or "").strip(),
                    author=(data.get("author") or "").strip(),
                    published_at=published_at,
                    view_count=0,
                    upvote_count=safe_int(data.get("ups")),
                    comment_count=safe_int(data.get("num_comments")),
                    raw_metadata={"source": "reddit", "subreddit": source_key},
                )
            )
        return posts

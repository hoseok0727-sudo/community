from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup

from app.collectors.base import RawPost
from app.collectors.utils import safe_int
from app.core.config import get_settings

logger = logging.getLogger(__name__)
KST = ZoneInfo("Asia/Seoul")


def parse_dc_datetime(raw: str, now: datetime | None = None) -> datetime:
    now = now or datetime.now(KST)
    value = (raw or "").strip()
    if not value:
        return now.astimezone(timezone.utc)

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S", "%Y.%m.%d", "%y.%m.%d"):
        try:
            parsed = datetime.strptime(value, fmt).replace(tzinfo=KST)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue

    if "." in value:
        parts = value.split(".")
        if len(parts) == 2:
            month, day = parts
            try:
                parsed = datetime(
                    year=now.year,
                    month=int(month),
                    day=int(day),
                    tzinfo=KST,
                )
                return parsed.astimezone(timezone.utc)
            except ValueError:
                pass

    if ":" in value:
        try:
            hour, minute = value.split(":")
            parsed = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass

    return now.astimezone(timezone.utc)


def parse_dcinside_list(html: str, source_key: str) -> list[RawPost]:
    soup = BeautifulSoup(html, "html.parser")
    posts: list[RawPost] = []

    rows = soup.select("tr.ub-content")
    for row in rows:
        gall_num = row.select_one("td.gall_num")
        if gall_num and "공지" in gall_num.get_text(strip=True):
            continue

        title_a = row.select_one("td.gall_tit a")
        if not title_a:
            continue

        title = title_a.get_text(" ", strip=True)
        if not title:
            continue

        href = title_a.get("href", "")
        url = urljoin("https://gall.dcinside.com", href)

        raw_external_id = row.get("data-no") or (gall_num.get_text(strip=True) if gall_num else "")
        if raw_external_id.isdigit():
            external_id = raw_external_id
        else:
            seed = f"{source_key}|{url}|{title}"
            external_id = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:20]

        comments = row.select_one(".reply_num")
        author = row.select_one(".gall_writer")
        date_node = row.select_one(".gall_date")
        count_node = row.select_one(".gall_count")
        rec_node = row.select_one(".gall_recommend")

        published_raw = date_node.get("title", "") if date_node else ""
        if not published_raw and date_node:
            published_raw = date_node.get_text(strip=True)

        post = RawPost(
            external_id=external_id,
            url=url,
            title=title,
            content="",
            author=author.get("data-nick", "") if author else "",
            published_at=parse_dc_datetime(published_raw),
            view_count=safe_int(count_node.get_text(strip=True) if count_node else "0"),
            upvote_count=safe_int(rec_node.get_text(strip=True) if rec_node else "0"),
            comment_count=safe_int(comments.get_text(strip=True) if comments else "0"),
            raw_metadata={"source": "dcinside", "gallery": source_key},
        )
        posts.append(post)

    return posts


class DcInsideCollector:
    source_type = "dcinside"

    def __init__(self) -> None:
        settings = get_settings()
        self.timeout = settings.http_timeout_seconds
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
        }

    def fetch_posts(self, source_key: str, limit: int = 100) -> list[RawPost]:
        page_size = min(max(limit, 10), 200)
        url = f"https://gall.dcinside.com/board/lists?id={source_key}"
        params = {"page": 1}

        with httpx.Client(
            timeout=self.timeout,
            headers=self.headers,
            follow_redirects=True,
        ) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            posts = parse_dcinside_list(response.text, source_key)

        if not posts:
            logger.warning("No posts parsed from dcinside gallery=%s", source_key)
        return posts[:page_size]

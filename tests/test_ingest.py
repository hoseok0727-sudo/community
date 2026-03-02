from datetime import datetime, timezone

from app.collectors.base import RawPost
from app.models import Gallery, Post
from app.services.ingest import collect_gallery_posts


class StubCollector:
    def __init__(self, payloads: list[RawPost]) -> None:
        self.payloads = payloads

    def fetch_posts(self, source_key: str, limit: int = 100) -> list[RawPost]:
        return self.payloads[:limit]


class StubRegistry:
    def __init__(self, collector) -> None:
        self.collector = collector

    def get(self, source_type: str):
        return self.collector


def _post(external_id: str, ups: int) -> RawPost:
    return RawPost(
        external_id=external_id,
        url=f"https://example.com/{external_id}",
        title=f"title-{external_id}",
        content="sample",
        author="u",
        published_at=datetime(2026, 3, 2, 10, 0, tzinfo=timezone.utc),
        upvote_count=ups,
        comment_count=1,
        view_count=10,
    )


def test_collect_gallery_posts_deduplicates(db_session):
    gallery = Gallery(
        source_type="reddit",
        source_key="python",
        display_name="Python",
        enabled=True,
    )
    db_session.add(gallery)
    db_session.commit()
    db_session.refresh(gallery)

    first_registry = StubRegistry(StubCollector([_post("1", 1), _post("2", 2)]))
    first_result = collect_gallery_posts(db_session, gallery, first_registry, limit=50)
    assert first_result.inserted_count == 2
    assert first_result.updated_count == 0

    second_registry = StubRegistry(StubCollector([_post("1", 9), _post("2", 7)]))
    second_result = collect_gallery_posts(db_session, gallery, second_registry, limit=50)
    assert second_result.inserted_count == 0
    assert second_result.updated_count == 2

    posts = db_session.query(Post).filter(Post.gallery_id == gallery.id).all()
    assert len(posts) == 2
    assert max(post.upvote_count for post in posts) == 9


from datetime import datetime, timedelta, timezone

from app.models import Gallery, Post
from app.services.briefing import build_briefing


def seed_gallery(db_session, source_type: str, source_key: str, name: str) -> Gallery:
    gallery = Gallery(
        source_type=source_type,
        source_key=source_key,
        display_name=name,
        enabled=True,
    )
    db_session.add(gallery)
    db_session.commit()
    db_session.refresh(gallery)
    return gallery


def seed_post(
    db_session,
    gallery_id: int,
    external_id: str,
    title: str,
    content: str,
    hours_ago: int,
) -> None:
    now = datetime.now(timezone.utc)
    db_session.add(
        Post(
            gallery_id=gallery_id,
            external_id=external_id,
            url=f"https://example.com/{external_id}",
            title=title,
            content=content,
            author="tester",
            published_at=now - timedelta(hours=hours_ago),
            view_count=100,
            upvote_count=10,
            comment_count=7,
            raw_metadata={},
        )
    )
    db_session.commit()


def test_build_briefing_for_selected_boards(db_session):
    first = seed_gallery(db_session, "dcinside", "programming", "DC Programming")
    second = seed_gallery(db_session, "reddit", "python", "Reddit Python")

    seed_post(
        db_session,
        first.id,
        "a1",
        "s26 heat issue",
        "many users mention heat and battery",
        1,
    )
    seed_post(
        db_session,
        second.id,
        "b1",
        "s26 battery heat discussion",
        "heat issue is repeated on reddit board",
        2,
    )

    briefing = build_briefing(
        db=db_session,
        gallery_ids=[first.id, second.id],
        window_hours=24,
        limit=10,
        per_gallery_cap=50,
    )

    assert briefing.topic_count >= 1
    assert len(briefing.selected_galleries) == 2
    top = briefing.topics[0]
    assert top.posts
    assert set(top.gallery_ids).issubset({first.id, second.id})

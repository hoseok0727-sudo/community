from datetime import timedelta

from app.models import Post
from app.services.topic_engine import build_topic_candidates


def make_post(idx: int, title: str, content: str, now_utc) -> Post:
    return Post(
        gallery_id=1,
        external_id=f"p-{idx}",
        url=f"https://example.com/{idx}",
        title=title,
        content=content,
        author="tester",
        published_at=now_utc - timedelta(hours=idx),
        view_count=10 + idx,
        upvote_count=2 + idx,
        comment_count=1 + idx,
        raw_metadata={},
    )


def test_build_topic_candidates_groups_similar_posts(now_utc):
    posts = [
        make_post(1, "갤럭시 s26 발열 이슈", "발열 때문에 프레임 드랍", now_utc),
        make_post(2, "갤럭시 s26 배터리 발열", "배터리 소모와 발열이 심함", now_utc),
        make_post(3, "s26 업데이트 발열 개선", "업데이트 이후 발열 변화", now_utc),
        make_post(4, "해외축구 경기 결과", "득점 장면 정리", now_utc),
    ]
    topics = build_topic_candidates(posts, window_hours=24)
    assert len(topics) >= 2
    assert max(len(t.posts) for t in topics) >= 2
    assert all(topic.title for topic in topics)


from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timezone

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models import Post
from app.services.scoring import compute_topic_score, post_engagement_score


@dataclass(slots=True)
class TopicCandidate:
    title: str
    summary: str
    keywords: list[str]
    confidence: float
    score: float
    trend: str
    posts: list[Post]


NOISE_PATTERNS = [
    re.compile(r"(.)\1{5,}"),
    re.compile(r"^[!?.~\s]+$"),
]


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s\uAC00-\uD7A3]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_likely_noise(title: str) -> bool:
    cleaned = title.strip()
    if len(cleaned) < 2:
        return True
    return any(pattern.search(cleaned) for pattern in NOISE_PATTERNS)


def _connected_components(sim_matrix: list[list[float]], threshold: float) -> list[list[int]]:
    n = len(sim_matrix)
    seen = [False] * n
    components: list[list[int]] = []
    for start in range(n):
        if seen[start]:
            continue
        stack = [start]
        seen[start] = True
        comp: list[int] = []
        while stack:
            node = stack.pop()
            comp.append(node)
            for nxt in range(n):
                if seen[nxt]:
                    continue
                if sim_matrix[node][nxt] >= threshold:
                    seen[nxt] = True
                    stack.append(nxt)
        components.append(sorted(comp))
    return components


def _extract_keywords(tfidf_matrix, indices: list[int], vectorizer: TfidfVectorizer) -> list[str]:
    if not indices:
        return []
    feature_names = vectorizer.get_feature_names_out()
    row = tfidf_matrix[indices].sum(axis=0)
    scores = row.A1
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [feature_names[i] for i in ranked if scores[i] > 0][:8]


def _cluster_confidence(sim_matrix: list[list[float]], indices: list[int]) -> float:
    if len(indices) <= 1:
        return 0.9
    sims: list[float] = []
    for i, left in enumerate(indices):
        for right in indices[i + 1 :]:
            sims.append(sim_matrix[left][right])
    if not sims:
        return 0.5
    avg = sum(sims) / len(sims)
    return max(0.05, min(round(avg, 4), 0.99))


def build_topic_candidates(posts: list[Post], window_hours: int) -> list[TopicCandidate]:
    if not posts:
        return []

    filtered = [post for post in posts if not is_likely_noise(post.title)]
    if not filtered:
        filtered = posts

    docs = [normalize_text(f"{post.title} {post.content}") for post in filtered]
    if len(filtered) == 1:
        score, trend = compute_topic_score(filtered, window_hours)
        post = filtered[0]
        return [
            TopicCandidate(
                title=post.title[:80],
                summary=f"Single-post topic detected: {post.title[:80]}",
                keywords=[word for word in normalize_text(post.title).split(" ") if word][:5],
                confidence=0.9,
                score=score,
                trend=trend,
                posts=filtered,
            )
        ]

    vectorizer = TfidfVectorizer(
        token_pattern=r"(?u)\b[\w\uAC00-\uD7A3]{2,}\b",
        max_features=3000,
        ngram_range=(1, 2),
    )
    try:
        tfidf = vectorizer.fit_transform(docs)
    except ValueError:
        return []

    sim = cosine_similarity(tfidf).tolist()
    clusters = _connected_components(sim, threshold=0.12)

    now = max((post.published_at for post in filtered), default=None)
    if now is None:
        return []
    now = now.astimezone(timezone.utc)

    results: list[TopicCandidate] = []
    for cluster_indices in clusters:
        cluster_posts = [filtered[idx] for idx in cluster_indices]
        cluster_posts.sort(
            key=lambda post: (post_engagement_score(post), post.published_at.timestamp()),
            reverse=True,
        )
        keywords = _extract_keywords(tfidf, cluster_indices, vectorizer)
        score, trend = compute_topic_score(cluster_posts, window_hours, now=now)
        representative_title = cluster_posts[0].title[:100]
        label = " / ".join(keywords[:3]) if keywords else representative_title[:50]
        summary = (
            f"{label} appears in {len(cluster_posts)} related posts. "
            f"Representative post: {representative_title}"
        )
        confidence = _cluster_confidence(sim, cluster_indices)
        results.append(
            TopicCandidate(
                title=label[:120],
                summary=summary[:500],
                keywords=keywords[:8],
                confidence=confidence,
                score=score,
                trend=trend,
                posts=cluster_posts[:10],
            )
        )

    results.sort(key=lambda item: item.score, reverse=True)
    return results


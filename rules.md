# rules.md

## 1) Compliance and Safety
- Respect target site policies and legal constraints.
- Use conservative crawl frequency and backoff on failures.
- Do not collect sensitive personal data beyond what is required for topic analysis.
- Keep request logs for operational debugging, not for user profiling.

## 2) Data Collection Rules
- Identify records with stable post IDs and enforce deduplication.
- Minimum crawler requirements:
  - timeout,
  - retry with exponential backoff,
  - per-gallery rate limit,
  - structured error logging.
- Do not block pipeline on single gallery failure.

## 3) Data Quality Rules
- Normalize text before analysis:
  - lowercase,
  - strip repeated punctuation,
  - remove common noise tokens.
- Drop or down-rank likely spam/bait posts.
- Keep raw title/content snapshots for reproducibility.

## 4) Topic Scoring Rules (Initial)
- Topic score should combine:
  - recency,
  - engagement (views/recommend/comments),
  - velocity (recent growth vs previous window).
- Keep scoring formula configurable from one place.
- Version scoring changes and record applied version in results.

## 5) Summary Rules
- Every topic summary must include:
  - one-line topic label,
  - 1-3 sentence summary,
  - 3-5 representative post links.
- If confidence is low, mark the summary as low confidence.
- Avoid definitive claims when evidence is weak or conflicting.

## 6) API Rules
- Keep response schemas explicit and versionable.
- Required endpoints in MVP:
  - GET /galleries
  - GET /topics?gallery=<id>&window=<hours>
  - GET /topic/{id}/posts
- Return timestamps in ISO-8601 UTC.

## 7) Engineering Quality
- Add tests for:
  - deduplication,
  - clustering behavior,
  - score computation.
- Use lint/format tooling and keep CI green before merge.
- No silent failures: errors must be visible in logs/metrics.

## 8) Definition of Done
- Feature is merged only when:
  - behavior is documented,
  - tests pass,
  - basic observability exists (logs/health checks),
  - rollback path is clear.


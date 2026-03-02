# Community Briefing API

Production-oriented backend for aggregating and summarizing fast-moving topics across multiple community sites.

Current supported sources:
- `dcinside` (gallery list parser)
- `reddit` (subreddit new posts)
- `hackernews` (Algolia API)

## What It Does
- Collects recent posts from configured sources on a schedule.
- Deduplicates posts by `(gallery_id, external_id)`.
- Builds topic clusters with TF-IDF + cosine similarity.
- Scores topics by engagement, recency, and velocity.
- Exposes API endpoints for galleries, topics, representative posts, and hourly trend buckets.

## Stack
- FastAPI
- SQLAlchemy 2.x
- APScheduler
- scikit-learn
- PostgreSQL or SQLite

## Project Structure
```text
app/
  api/          # HTTP endpoints
  collectors/   # Source-specific collectors
  services/     # Ingest + topic engine + scoring
  core/         # Settings + logging
  db.py         # DB session/engine
  models.py     # ORM models
  main.py       # FastAPI app entry
scripts/
  seed_galleries.py
tests/
```

## Local Run
1. Install dependencies
```bash
python -m pip install -e .[dev]
```

2. Create environment file
```bash
copy .env.example .env
```

3. Start API
```bash
uvicorn app.main:app --reload
```

Health check:
```bash
curl http://127.0.0.1:8000/health
```

## Docker Run (PostgreSQL)
```bash
docker compose up --build
```

## Register Sources
### Via API
```bash
curl -X POST http://127.0.0.1:8000/galleries ^
  -H "Content-Type: application/json" ^
  -d "{\"source_type\":\"reddit\",\"source_key\":\"python\",\"display_name\":\"Python Reddit\"}"
```

### Via script
```bash
python scripts/seed_galleries.py ^
  --gallery reddit:python:Python-Reddit ^
  --gallery hackernews:ai:HN-AI ^
  --gallery dcinside:programming:DC-Programming
```

## Trigger Pipeline
```bash
curl -X POST "http://127.0.0.1:8000/ops/collect"
curl -X POST "http://127.0.0.1:8000/ops/topics/rebuild?window_hours=24"
```

If `ADMIN_API_KEY` is set in `.env`, send `X-API-Key` header to `/ops/*`.

## Read API Data
```bash
curl "http://127.0.0.1:8000/galleries"
curl "http://127.0.0.1:8000/topics?gallery_id=1&window_hours=24"
curl "http://127.0.0.1:8000/topic/1/posts"
curl "http://127.0.0.1:8000/topics/trend?gallery_id=1&hours=24"
```

## Quality Gate
```bash
python -m ruff check .
python -m pytest
```

## Notes for Real Production
- Check each site's policy and legal constraints before large-scale collection.
- Keep strict rate limits and retry/backoff settings.
- Add distributed workers + queue when traffic grows.
- Add alerting/metrics and migration tooling (Alembic) before high-scale launch.


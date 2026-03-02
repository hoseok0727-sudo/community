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
- Lets users select multiple boards and generates one combined briefing for those boards.
- Exposes API endpoints for board registration, briefing, and hourly trend buckets.
- Serves a web dashboard at `/` for end-to-end testing without separate frontend setup.

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

Dashboard:
```text
http://127.0.0.1:8000/
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
curl "http://127.0.0.1:8000/briefing?gallery_ids=1&gallery_ids=2&window_hours=24&limit=20"
curl "http://127.0.0.1:8000/topics?gallery_id=1&window_hours=24"
curl "http://127.0.0.1:8000/topic/1/posts"
curl "http://127.0.0.1:8000/topics/trend?gallery_id=1&hours=24"
```

## Dashboard Test Flow
1. Open `http://127.0.0.1:8000/`.
2. Add boards in `Board Setup`.
3. Click `Collect Posts` to fetch new posts.
4. Select boards in `Select Boards`.
5. Click `Generate Briefing` to get one summarized topic list for selected boards.
6. Click a topic card and verify `Evidence Posts`.

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

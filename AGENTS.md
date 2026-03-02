# AGENTS.md

## Project
- Name: DC Gall Briefing
- Goal: Aggregate and summarize major topics ("tteokbab"/ongoing discussion themes) across selected DCInside galleries so users can quickly understand what happened in a time window.

## Product Scope (MVP)
- User registers 1-3 galleries.
- System collects recent posts on a schedule.
- System groups similar posts into topic clusters.
- System provides:
  - top topics by gallery,
  - short summary per topic,
  - representative post links,
  - simple trend over time.

## Agent Roles
- Planner agent:
  - Break work into small deliverable steps.
  - Keep API and data model stable while iterating internals.
- Collector agent:
  - Implement gallery crawling/fetching with strict rate limiting.
  - Preserve raw response metadata for debugging.
- Topic agent:
  - Build clustering + keyword extraction + summary pipeline.
  - Prefer deterministic baseline first, then optional LLM enhancement.
- API/UI agent:
  - Expose query endpoints and dashboard views.
  - Keep UX focused on "quick understanding in one screen."

## Operating Principles
- Start simple, then improve:
  - First working version must avoid unnecessary complexity.
- Keep traceability:
  - Every topic summary must link back to representative posts.
- Be robust to noisy community data:
  - Deduplicate repeated titles/content and filter obvious spam.
- Optimize for recency:
  - Favor recent momentum over total historical volume.

## Suggested Tech Baseline
- Backend: Python + FastAPI
- Storage: PostgreSQL
- Scheduling: APScheduler (upgrade later if needed)
- Similarity baseline: TF-IDF + cosine similarity
- Frontend: Next.js dashboard

## Handoff Checklist
- Update README when architecture or setup changes.
- Add or update tests for changed logic.
- Provide a short runbook section for new scripts/services.
- Document known limitations and next improvement point.


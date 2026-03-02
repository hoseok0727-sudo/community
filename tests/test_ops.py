from app.api import ops
from app.services.ingest import IngestResult


def test_run_collect_serializes_ingest_result(monkeypatch, db_session):
    def fake_collect_enabled_galleries(db, registry, limit):
        return [
            IngestResult(
                gallery_id=1,
                fetched_count=10,
                inserted_count=7,
                updated_count=3,
            )
        ]

    monkeypatch.setattr(ops, "collect_enabled_galleries", fake_collect_enabled_galleries)
    result = ops.run_collect(gallery_id=None, limit=100, db=db_session)
    assert len(result) == 1
    assert result[0].gallery_id == 1
    assert result[0].inserted_count == 7
    assert result[0].updated_count == 3


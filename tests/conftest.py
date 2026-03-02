from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    session = session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def now_utc() -> datetime:
    return datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc)


from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app import db


@pytest.fixture
def engine() -> Generator[Engine, None, None]:
    eng = db.make_engine()
    db.Base.metadata.create_all(eng)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture
def session(engine: Engine) -> Generator[Session, None, None]:
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    from app.main import app

    def _override() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[db.get_session] = _override
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()

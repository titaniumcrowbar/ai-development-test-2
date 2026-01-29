from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import DataAction
from app.seed_data import DATA_ACTION_SEEDS


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    for seed in DATA_ACTION_SEEDS:
        session.add(DataAction(name=seed.name, lookup_value=seed.lookup_value, is_active=True))
    session.commit()
    try:
        yield session
    finally:
        session.close()

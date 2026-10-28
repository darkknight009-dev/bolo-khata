"""SQLite engine/session helpers."""
from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, create_engine

from . import config

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        config.ensure_dirs()
        engine = create_engine(config.db_url(), echo=False)
        # Import models so SQLModel.metadata sees them before create_all
        from . import models as _m  # noqa: F401

        engine.connect().exec_driver_sql("PRAGMA journal_mode=WAL;")
        from sqlmodel import SQLModel

        SQLModel.metadata.create_all(engine)
        _engine = engine
    return _engine


@contextmanager
def get_session() -> Iterator[Session]:
    # expire_on_commit=False: instances stay usable after the session closes,
    # which the background runner relies on.
    with Session(get_engine(), expire_on_commit=False) as session:
        yield session

"""SQLite engine, session factory, and FastAPI dependency."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATA_DIR, get_settings

settings = get_settings()

# check_same_thread=False is required for SQLite under FastAPI's thread pool.
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

# Ensure the on-disk data dir exists for the default sqlite:///.../data/fitos.db path.
DATA_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create all tables. Import models first so they register on Base.metadata."""
    from app import models  # noqa: F401  (side-effect import)

    Base.metadata.create_all(bind=engine)
    _add_missing_analysis_columns()


# Columns added to review_analysis after the first release. create_all() only
# creates missing tables, so pre-existing databases need an additive ALTER.
_ANALYSIS_COLUMNS = {
    "analysis_source": "VARCHAR",
    "analysis_mode": "VARCHAR",
    "elapsed_seconds": "FLOAT",
}


def _add_missing_analysis_columns() -> None:
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if not inspector.has_table("review_analysis"):
        return
    existing = {col["name"] for col in inspector.get_columns("review_analysis")}
    with engine.begin() as conn:
        for name, sql_type in _ANALYSIS_COLUMNS.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE review_analysis ADD COLUMN {name} {sql_type}"))


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

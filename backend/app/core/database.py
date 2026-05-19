from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.core.config import PROJECT_ROOT, get_settings


class Base(DeclarativeBase):
    pass


def _normalize_database_url(url: str) -> str:
    # Render and Railway often expose postgres://, while SQLAlchemy expects postgresql://.
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


settings = get_settings()
database_url = _normalize_database_url(settings.database_url)

if database_url.startswith("sqlite:///"):
    db_file = database_url.replace("sqlite:///", "", 1)
    Path(db_file).parent.mkdir(parents=True, exist_ok=True)

engine_args = {"connect_args": {"check_same_thread": False}} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, pool_pre_ping=True, future=True, **engine_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def init_db() -> None:
    # Import models before create_all so SQLAlchemy knows every table.
    from backend.app import models  # noqa: F401

    (PROJECT_ROOT / "database").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


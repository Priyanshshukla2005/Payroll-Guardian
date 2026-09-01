"""Database engine, session factory, and lifecycle management (Phase 10)."""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.config.settings import settings

logger = logging.getLogger("payroll_guardian.db")

# Create declarative base
Base = declarative_base()

# Configure engine with SQLite and PostgreSQL support
db_url = settings.database_url
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    logger.info(f"Initializing database schema on {db_url}...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")

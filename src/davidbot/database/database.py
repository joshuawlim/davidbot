"""Database connection and session management."""

import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import logging

from .models import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine = None
_SessionLocal = None


def get_database_url() -> str:
    """Get database URL from environment or use default SQLite path."""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    # Default to local SQLite in data directory
    project_root = Path(__file__).parent.parent.parent.parent
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / "davidbot.db"
    return f"sqlite:///{db_path}"


def get_engine() -> Engine:
    """Get or create SQLAlchemy engine."""
    global _engine
    
    if _engine is None:
        database_url = get_database_url()
        logger.info(f"Connecting to database: {database_url}")
        
        # SQLite-specific configuration
        if database_url.startswith("sqlite"):
            _engine = create_engine(
                database_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                connect_args={
                    "check_same_thread": False,  # Allow multi-threading
                    "timeout": 20,  # 20 second timeout
                }
            )
            
            # Enable foreign key constraints for SQLite
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")  # Better concurrency
                cursor.close()
        else:
            _engine = create_engine(database_url, echo=False, pool_pre_ping=True)
    
    return _engine


def get_session_factory():
    """Get or create session factory."""
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return _SessionLocal


def get_session() -> Session:
    """Get a new database session."""
    SessionLocal = get_session_factory()
    return SessionLocal()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session with context manager for automatic cleanup."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database() -> None:
    """Initialize database tables."""
    engine = get_engine()
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def reset_database() -> None:
    """Reset database by dropping and recreating all tables."""
    engine = get_engine()
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database reset completed")


def backup_database(backup_path: str) -> None:
    """Create a backup of the SQLite database."""
    if not get_database_url().startswith("sqlite"):
        raise ValueError("Backup only supported for SQLite databases")
    
    import shutil
    database_url = get_database_url()
    db_path = database_url.replace("sqlite:///", "")
    
    shutil.copy2(db_path, backup_path)
    logger.info(f"Database backed up to: {backup_path}")


def get_database_info() -> dict:
    """Get database connection information."""
    database_url = get_database_url()
    engine = get_engine()
    
    info = {
        "url": database_url,
        "driver": engine.dialect.name,
        "database_exists": os.path.exists(database_url.replace("sqlite:///", "")) if database_url.startswith("sqlite") else True,
    }
    
    # Get table info if database exists
    if info["database_exists"]:
        with get_db_session() as session:
            # Count records in each table
            from .models import Song, Lyrics, UserFeedback, SongUsage, ThemeMapping, MessageLog
            info["tables"] = {
                "songs": session.query(Song).count(),
                "lyrics": session.query(Lyrics).count(),
                "user_feedback": session.query(UserFeedback).count(),
                "song_usage": session.query(SongUsage).count(),
                "theme_mappings": session.query(ThemeMapping).count(),
                "message_logs": session.query(MessageLog).count(),
            }
    
    return info
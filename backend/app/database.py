"""
CKSEARCH API - Database Connection
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# Lazy initialization
_engine = None
_SessionLocal = None


def get_database_url():
    """Get database URL from environment."""
    url = os.getenv("DATABASE_URL", "")
    
    # Handle Railway's postgres:// vs postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    
    return url


def get_engine():
    """Get or create database engine (lazy)."""
    global _engine
    if _engine is None:
        url = get_database_url()
        if url:
            _engine = create_engine(url, pool_pre_ping=True)
        else:
            raise ValueError("DATABASE_URL environment variable is not set")
    return _engine


def get_session_local():
    """Get or create session factory (lazy)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db():
    """Dependency untuk mendapatkan database session."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

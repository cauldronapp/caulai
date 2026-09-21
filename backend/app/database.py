"""SQLAlchemy engine/session bound to the environment-selected PostgreSQL database."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import get_runtime_database_url


class Base(DeclarativeBase):
    pass


engine = create_engine(
    get_runtime_database_url(),
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

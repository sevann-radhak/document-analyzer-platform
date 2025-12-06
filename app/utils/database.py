from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
from app.core.config import settings

database_url = settings.get_database_url()

if "sqlserver" in database_url:
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.debug,
        connect_args={"timeout": 30}
    )
else:
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        echo=settings.debug
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


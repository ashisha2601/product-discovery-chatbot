from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import get_settings


settings = get_settings()


class Base(DeclarativeBase):
    pass


# Ensure SQLAlchemy uses psycopg (psycopg3) driver on Postgres so we are
# compatible with newer Python runtimes like 3.13 on Render.
database_url = settings.database_url
url = make_url(database_url)

if url.drivername == "postgresql":
    url = url.set(drivername="postgresql+psycopg")

engine = create_engine(url, echo=False, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



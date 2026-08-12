"""Dependencias de FastAPI.

Fuente única de la sesión de BD y las factorías de repositorios, para que los
routers dependan de abstracciones y no de `SessionLocal` directamente.
"""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from db.database import SessionLocal
from lib.repository import (
    ArtistRepository,
    EventRepository,
    FeedRepository,
    LinkRepository,
)


def get_db() -> Generator[Session, None, None]:
    """Crea una sesión por petición y la cierra al terminar."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_artist_repo(session: Session = Depends(get_db)) -> ArtistRepository:
    return ArtistRepository(session)


def get_event_repo(session: Session = Depends(get_db)) -> EventRepository:
    return EventRepository(session)


def get_feed_repo(session: Session = Depends(get_db)) -> FeedRepository:
    return FeedRepository(session)


def get_link_repo(session: Session = Depends(get_db)) -> LinkRepository:
    return LinkRepository(session)
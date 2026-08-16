"""Conexión a la base de datos.

La capa de datos usa SQLAlchemy para que el cambio de SQLite (desarrollo) a
PostgreSQL (crecimiento nacional/internacional) sea transparente.
"""

import os

import dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

dotenv.load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///instance/local_scene.db"
)

# Neon entrega `postgres://`/`postgresql://`; SQLAlchemy usa el driver
# `psycopg` (v3) declarándolo explícitamente en el dialecto.
if DATABASE_URL.startswith(("postgres://", "postgresql://")):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://", "postgresql+psycopg://", 1
    ).replace("postgresql://", "postgresql+psycopg://", 1)

# Para SQLite hay que permitir que varios hilos de Streamlit usen la conexión.
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs = {"connect_args": {"check_same_thread": False}}

engine = create_engine(DATABASE_URL, future=True, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Asegura que existan todas las tablas al arrancar (seed opcional).
from db.models import Base  # noqa: E402

Base.metadata.create_all(engine)


def _asegurar_columnas_extra():
    """Migración ligera: agrega columnas nuevas a tablas ya existentes."""
    if not DATABASE_URL.startswith("sqlite"):
        from sqlalchemy import text

        inspector = inspect(engine)
        if "feed_items" in inspector.get_table_names():
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE feed_items ALTER COLUMN imagen TYPE TEXT")
                )
        if "artists" in inspector.get_table_names():
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE artists ADD COLUMN IF NOT EXISTS "
                        "oyentes_mensuales_spotify INTEGER"
                    )
                )
                conn.execute(
                    text(
                        "ALTER TABLE artists ADD COLUMN IF NOT EXISTS "
                        "fecha_oyentes_spotify TIMESTAMP"
                    )
                )
                conn.execute(
                    text(
                        "ALTER TABLE artists ADD COLUMN IF NOT EXISTS "
                        "fuente_oyentes_spotify VARCHAR(80)"
                    )
                )
                conn.execute(
                    text(
                        "ALTER TABLE artists ADD COLUMN IF NOT EXISTS "
                        "followers_beatport INTEGER"
                    )
                )
                conn.execute(
                    text(
                        "ALTER TABLE artists ADD COLUMN IF NOT EXISTS "
                        "followers_mixcloud INTEGER"
                    )
                )
                conn.execute(
                    text(
                        "ALTER TABLE artists ADD COLUMN IF NOT EXISTS "
                        "tt_user_id VARCHAR(120)"
                    )
                )
                conn.execute(
                    text(
                        "ALTER TABLE artists ADD COLUMN IF NOT EXISTS "
                        "tt_refresh_token VARCHAR(500)"
                    )
                )
        return
    from sqlalchemy import text

    inspector = inspect(engine)
    if "feed_items" in inspector.get_table_names():
        columnas = {c["name"] for c in inspector.get_columns("feed_items")}
        if "imagen" not in columnas:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE feed_items ADD COLUMN imagen VARCHAR(500)")
                )
    if "artists" in inspector.get_table_names():
        columnas = {c["name"] for c in inspector.get_columns("artists")}
        if "bio" not in columnas:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE artists ADD COLUMN bio TEXT"))
        if "imagen_perfil" not in columnas:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE artists ADD COLUMN imagen_perfil VARCHAR(500)")
                )
                conn.execute(
                    text("ALTER TABLE artists ADD COLUMN imagen_origen VARCHAR(30)")
                )
                conn.execute(
                    text(
                        "ALTER TABLE artists ADD COLUMN imagen_actualizada DATETIME"
                    )
                )
        for columna in ("fb_page_id", "fb_page_token", "ig_user_id"):
            if columna not in columnas:
                with engine.begin() as conn:
                    conn.execute(
                        text(f"ALTER TABLE artists ADD COLUMN {columna} VARCHAR(500)")
                    )
        for columna in ("tt_user_id", "tt_refresh_token"):
            if columna not in columnas:
                with engine.begin() as conn:
                    conn.execute(
                        text(f"ALTER TABLE artists ADD COLUMN {columna} VARCHAR(500)")
                    )
        for columna, tipo in (
            ("oyentes_mensuales_spotify", "INTEGER"),
            ("fecha_oyentes_spotify", "DATETIME"),
            ("fuente_oyentes_spotify", "VARCHAR(80)"),
        ):
            if columna not in columnas:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE artists ADD COLUMN {columna} {tipo}"))
        for columna, tipo in (
            ("followers_beatport", "INTEGER"),
            ("followers_mixcloud", "INTEGER"),
        ):
            if columna not in columnas:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE artists ADD COLUMN {columna} {tipo}"))


_asegurar_columnas_extra()

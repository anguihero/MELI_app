"""
SQLAlchemy models and database initialization for MELI app.
Handles database connection, model definitions, and table creation.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    create_engine,
    DateTime,
    Enum,
    ForeignKey,
    Float,
    func,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import inspect


# ============================================================================
# SECTION 1: DATABASE CONFIGURATION
# ============================================================================

# Default SQLite path (used only when DATABASE_URL is not provided)
DEFAULT_DB_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "database.db"

# Build DB URL from env or fallback to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Global engine and session factory
engine = None
SessionLocal = None


# ============================================================================
# SECTION 2: DECLARATIVE BASE
# ============================================================================

class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy models."""
    pass


# ============================================================================
# SECTION 3: DATA MODELS
# ============================================================================

class Item(Base):
    """Table for storing marketplace items."""
    __tablename__ = "items"

    # Auto-incremented primary key
    id: Mapped[str] = mapped_column(String, primary_key=True)
    
    # Foreign key: item identifier string
    id_item: Mapped[str] = mapped_column(String, primary_key=True)
    # Item title with unique constraint
    title: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    # Record creation timestamp with timezone
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    # Record last update timestamp with automatic update
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )


class Match(Base):
    """Table for storing similarity matches between items."""
    __tablename__ = "matches"

    # Auto-incremented primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Foreign key to first item
    id_item_1: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    # Cached title of first item for performance
    title_item_1: Mapped[str] = mapped_column(String, nullable=False)
    # Foreign key to second item
    id_item_2: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    # Cached title of second item for performance
    title_item_2: Mapped[str] = mapped_column(String, nullable=False)
    # Similarity score between 0 and 1
    score: Mapped[float] = mapped_column(Float, nullable=False)
    # Match status: positive, in progress, or negative
    status: Mapped[Enum] = mapped_column(
        Enum("positivo", "en progreso", "negativo", name="match_status_enum"), 
        nullable=False
    )
    # Record creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    # Record last update timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )


class MatchBackup(Base):
    """Table for storing backup copies of matches."""
    __tablename__ = "matches_backup"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_item_1: Mapped[str] = mapped_column(String, nullable=False)
    title_item_1: Mapped[str] = mapped_column(String, nullable=False)
    id_item_2: Mapped[str] = mapped_column(String, nullable=False)
    title_item_2: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[Enum] = mapped_column(
        Enum("positivo", "en progreso", "negativo", name="match_backup_status_enum"), 
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    restored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


# ============================================================================
# SECTION 4: DATABASE INITIALIZATION
# ============================================================================

def migrate_sqlite_to_engine(target_sessionmaker, target_engine):
    """Copy data from local SQLite file into the target engine if present."""
    source_path = Path(os.getenv("SQLITE_MIGRATION_PATH", DEFAULT_DB_PATH))
    if not source_path.exists():
        print(f"No SQLite migration file found at {source_path}; skipping migration.")
        return

    sqlite_url = f"sqlite:///{source_path}"
    sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, echo=False)
    SourceSession = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)

    src = SourceSession()
    dst = target_sessionmaker()

    try:
        for Model in (Item, Match, MatchBackup):
            target_count = dst.query(Model).count()
            if target_count:
                print(f"Skipping {Model.__tablename__} migration; target already has data ({target_count}).")
                continue

            rows = src.query(Model).all()
            if not rows:
                continue

            for row in rows:
                data = {col.name: getattr(row, col.name) for col in Model.__table__.columns}
                dst.merge(Model(**data))
            dst.commit()
            print(f"Migrated {len(rows)} rows into {Model.__tablename__}.")
        
        # Reset PostgreSQL sequences to prevent ID duplication
        if not str(target_engine.url).startswith("sqlite"):
            with target_engine.connect() as conn:
                conn.execute(text("SELECT setval('matches_id_seq', (SELECT MAX(id) FROM matches));"))
                conn.commit()
                print("✓ PostgreSQL sequence reset successfully.")
    finally:
        dst.close()
        src.close()
        sqlite_engine.dispose()


def ensure_postgres_schema(target_engine):
    """Fuerza la eliminación de la restricción de unicidad en ID y configura PK compuesta."""
    inspector = inspect(target_engine)
    if "items" not in inspector.get_table_names():
        return

    print("Verificando integridad de la tabla 'items' en Postgres...")
    
    with target_engine.connect() as conn:
        # 1. Asegurar que id_item existe
        cols = {c["name"] for c in inspector.get_columns("items")}
        if "id_item" not in cols:
            conn.execute(text("ALTER TABLE items ADD COLUMN id_item VARCHAR"))
            conn.commit()

        # 2. Rellenar id_item si está vacío
        conn.execute(text("UPDATE items SET id_item = id WHERE id_item IS NULL"))
        
        # 3. ELIMINAR CUALQUIER RESTRICCIÓN O ÍNDICE QUE BLOQUEE EL ID
        # Ejecutamos comandos SQL puros para limpiar el rastro de 'items_id_key'
        commands = [
            "ALTER TABLE matches DROP CONSTRAINT IF EXISTS matches_id_item_1_fkey",
            "ALTER TABLE matches DROP CONSTRAINT IF EXISTS matches_id_item_2_fkey",
            "ALTER TABLE items DROP CONSTRAINT IF EXISTS items_id_key CASCADE",
            "DROP INDEX IF EXISTS items_id_key",
            "ALTER TABLE items DROP CONSTRAINT IF EXISTS items_pkey CASCADE",
            "ALTER TABLE items DROP CONSTRAINT IF EXISTS items_title_key CASCADE" # Por si los títulos se repiten
        ]
        
        for cmd in commands:
            try:
                conn.execute(text(cmd))
                conn.commit()
            except Exception as e:
                print(f"Nota: No se pudo ejecutar '{cmd}' (probablemente ya no existe).")

        # 4. APLICAR LA NUEVA LLAVE PRIMARIA COMPUESTA
        print("Aplicando nueva Primary Key compuesta (id, id_item)...")
        try:
            conn.execute(text("ALTER TABLE items ADD PRIMARY KEY (id, id_item)"))
            conn.commit()
            print("✓ Configuración de base de datos exitosa.")
        except Exception as e:
            print(f"Error al crear la PK: {e}")

def init_db(database_url: Optional[str] = None):
    """
    Initialize database connection using env DATABASE_URL when provided
    (PostgreSQL in docker-compose) or fallback to local SQLite.
    Always ensures tables exist.
    """
    global engine, SessionLocal

    url = database_url or DATABASE_URL
    is_sqlite = url.startswith("sqlite:///")

    # For SQLite, ensure directory exists and detect prior file
    if is_sqlite:
        db_file = Path(url.replace("sqlite:///", "", 1))
        db_file.parent.mkdir(parents=True, exist_ok=True)
        db_exists = db_file.exists()
        print(f"Database path: {db_file}")
        print(f"Database exists: {db_exists}")
    else:
        db_exists = None
        print(f"Database URL: {url}")

    engine_kwargs = {"echo": False}
    if is_sqlite:
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    try:
        engine = create_engine(url, **engine_kwargs)
        with engine.connect() as conn:
            if is_sqlite:
                conn.execute("PRAGMA foreign_keys = ON")
            print("✓ Database connection successful.")
    except Exception as e:
        print(f"✗ Error connecting to database: {e}")
        exit(1)

    # Always ensure tables are present (safe if they already exist)
    print("Ensuring database tables exist...")
    Base.metadata.create_all(engine)
    print("✓ Database tables ready.")

    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # If we're targeting Postgres (or any non-SQLite URL), migrate data from local SQLite if available
    if not is_sqlite:
        ensure_postgres_schema(engine)
        migrate_sqlite_to_engine(SessionLocal, engine)

    print("✓ Database initialization completed.")
    return engine, SessionLocal


# ============================================================================
# SECTION 5: MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    init_db()

from __future__ import annotations

import enum
from datetime import datetime
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
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import os
import time

# --- Modelos de SQLAlchemy ---
class Base(DeclarativeBase):
    """Declarative base for all models."""


class Item(Base):
    """Table for storing items."""
    __tablename__ = "items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )


class Match(Base):
    """Table for storing matches."""
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_item_1: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    title_item_1: Mapped[str] = mapped_column(String, nullable=False)
    id_item_2: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    title_item_2: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[Enum] = mapped_column(
        Enum("positivo", "en progreso", "negativo", name="match_status_enum"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )


class MatchBackup(Base):
    """Table for storing match backups."""
    __tablename__ = "matches_backup"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_item_1: Mapped[str] = mapped_column(String, nullable=False)
    title_item_1: Mapped[str] = mapped_column(String, nullable=False)
    id_item_2: Mapped[str] = mapped_column(String, nullable=False)
    title_item_2: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[Enum] = mapped_column(
        Enum("positivo", "en progreso", "negativo", name="match_backup_status_enum"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    restored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

# --- Lógica de Inicialización ---
def init_db():
    """
    Inicializa la base de datos, esperando a que esté disponible
    y creando las tablas si no existen.
    """
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("No se encontró la variable de entorno DATABASE_URL")

    print("Iniciando inicialización de la base de datos...")
    
    # Reintentos para conectar a la base de datos
    engine = None
    for i in range(10):
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as connection:
                print("Conexión a la base de datos exitosa.")
                break
        except Exception as e:
            print(f"Intento {i+1}/10: No se pudo conectar a la base de datos: {e}")
            if i < 9:
                print("Reintentando en 5 segundos...")
                time.sleep(5)
            else:
                print("Error: No se pudo establecer conexión con la base de datos después de varios intentos.")
                exit(1)

    # Crear todas las tablas
    print("Creando tablas basadas en los modelos de SQLAlchemy...")
    Base.metadata.create_all(engine)
    print("Tablas creadas exitosamente.")
    print("Inicialización de la base de datos completada.")

if __name__ == "__main__":
    init_db()

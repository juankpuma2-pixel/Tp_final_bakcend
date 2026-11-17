"""
Módulo de conexión de Base de Datos para Servicios (app/services/database.py)
=============================================================================
Conecta al archivo local 'tienda.db' en la raíz del proyecto usando SQLite y
configura connect_args={"check_same_thread": False} para compatibilidad con FastAPI.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings
from app.database import (
    SQLALCHEMY_DATABASE_URL,
    engine,
    SessionLocal,
    Base,
    get_db,
)

__all__ = [
    "SQLALCHEMY_DATABASE_URL",
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "create_engine",
    "sessionmaker",
    "declarative_base",
]

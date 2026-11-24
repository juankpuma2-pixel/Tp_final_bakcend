import os
from pathlib import Path
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# ---------------------------------------------------------------------------
# Resolución de ruta ABSOLUTA a tienda.db — anclada a la raíz del proyecto.
# Esto garantiza que FastAPI siempre lea/escriba el MISMO archivo sin importar
# desde qué directorio se inicie uvicorn, pytest o scripts auxiliares.
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent   # raíz: clase9_ecomerce-main/

_config_db_url = settings.DATABASE_URL or "sqlite:///./tienda.db"

if _config_db_url.startswith("sqlite"):
    # Extraemos el nombre del archivo (tienda.db, ecommerce.db, etc.)
    db_name = (
        _config_db_url
        .replace("sqlite:///./", "")
        .replace("sqlite:///", "")
        .replace("sqlite://", "")
    )
    # Si el nombre ya es una ruta absoluta la usamos directamente
    if os.path.isabs(db_name):
        DB_PATH = db_name
    else:
        DB_PATH = str((BASE_DIR / db_name).resolve())

    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
else:
    if _config_db_url.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = _config_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif _config_db_url.startswith("postgresql://") and not _config_db_url.startswith("postgresql+"):
        SQLALCHEMY_DATABASE_URL = _config_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        SQLALCHEMY_DATABASE_URL = _config_db_url
    DB_PATH = None

# ---------------------------------------------------------------------------
# Creación del Engine
# - check_same_thread=False   → requerido para FastAPI (multi-thread)
# - WAL journal mode          → permite lectores concurrentes (DBeaver) sin
#                               bloquear al escritor y evita archivos -shm/-wal
#                               visibles en exploradores externos.
# - synchronous=NORMAL        → balance entre durabilidad y rendimiento en WAL.
# ---------------------------------------------------------------------------
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        pool_recycle=300,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragmas(dbapi_connection, connection_record):
        """
        Configura SQLite en modo WAL al establecer cada conexión.
        WAL (Write-Ahead Log) permite que DBeaver u otras herramientas lean
        la BD mientras FastAPI escribe, eliminando el problema de desincronización.
        """
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")    # lecturas concurrentes sin bloqueo
        cursor.execute("PRAGMA synchronous=NORMAL;")  # flush en modo WAL es seguro
        cursor.execute("PRAGMA foreign_keys=ON;")     # integridad referencial
        cursor.close()
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
    )

# ---------------------------------------------------------------------------
# Session factory y Base declarativa
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------------------------------------------------------------------------
# Mensaje de arranque: ruta exacta del archivo .db impresa en consola.
# Úsala en DBeaver → Nueva Conexión → SQLite → seleccionar este archivo.
# ---------------------------------------------------------------------------
if DB_PATH:
    print("=" * 70)
    print("  [DATABASE] SQLite conectado en:")
    print(f"  {DB_PATH}")
    print("  Pega esta ruta en DBeaver para abrir la base de datos correcta.")
    print("=" * 70)


# ---------------------------------------------------------------------------
# Generador de sesión para FastAPI (Depends)
# La sesión se cierra en el bloque finally — siempre, incluso ante errores.
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

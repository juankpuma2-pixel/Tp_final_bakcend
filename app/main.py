import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import Base, engine, DB_PATH, SQLALCHEMY_DATABASE_URL, get_db
from app.core.config import settings
from app.routers import productos, auth, pedidos, usuarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación: startup y shutdown."""
    # --- STARTUP ---
    # 1. Crear todas las tablas si no existen
    Base.metadata.create_all(bind=engine)

    # Migración segura en SQLite para nueva columna Ley 25.326 si no existe
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                res = conn.execute(text("PRAGMA table_info(usuarios);")).fetchall()
                cols = [r[1] for r in res]
                if "acepta_politica_privacidad" not in cols:
                    conn.execute(text("ALTER TABLE usuarios ADD COLUMN acepta_politica_privacidad BOOLEAN NOT NULL DEFAULT 0;"))
                    conn.commit()
        except Exception:
            pass

    # 2. Imprimir ruta exacta del archivo .db para configurar DBeaver
    if DB_PATH:
        print("=" * 70)
        print("  [DATABASE] SQLite activo en ruta absoluta:")
        print(f"  {DB_PATH}")
        print("  -> Copia esta ruta en DBeaver: Nueva Conexion > SQLite > Database File")
        print("=" * 70)

    yield

    # --- SHUTDOWN ---
    # Forzar checkpoint WAL para que todos los cambios queden en el .db principal
    # antes de que uvicorn termine. Esto asegura que DBeaver siempre lea el estado final.
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE);"))
        except Exception:
            pass


# Instanciamos la app con el título del .env y el ciclo de vida
app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Middleware CORS cargado dinámicamente desde .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API Backend Ecommerce activa", "docs": "/docs"}

@app.get("/salud", tags=["Salud"])
def salud(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"estado": "ok", "base": "ok"}

# Parte 3: Incluimos las rutas de productos
app.include_router(productos.router)

# Clase 7: Incluimos las rutas de autenticación
app.include_router(auth.router)

# Clase 8: Incluimos las rutas de pedidos y checkout
app.include_router(pedidos.router)

# Incluimos las rutas de usuarios
app.include_router(usuarios.router)

# Clase 10: Archivos estáticos — sirve uploads/ bajo el prefijo /static
# Ejemplo: uploads/productos/1-abc123.jpg → http://host/static/productos/1-abc123.jpg
Path("uploads/productos").mkdir(parents=True, exist_ok=True)
_UPLOADS_DIR = Path("uploads")
_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_UPLOADS_DIR)), name="static")

_DEMO_DIR = Path("app/static/demo")
_DEMO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/demo", StaticFiles(directory=str(_DEMO_DIR)), name="demo")
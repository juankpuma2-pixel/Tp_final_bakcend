"""
Script de Semillero (Seed) para Producción (Render / PostgreSQL / SQLite)
========================================================================
Puebla la base de datos de manera idempotente:
- Crea o verifica el usuario Administrador a partir de las variables de entorno
  SEED_ADMIN_EMAIL y SEED_ADMIN_PASSWORD.
- Si existen archivos en app/static/demo, o se definen productos de demostración,
  inserta los productos verificando antes por nombre para evitar duplicados.
- El campo imagen_url de cada producto apunta a /demo/<nombre_del_archivo>.
- Al finalizar el commit imprime "Seed listo." y cierra la sesión.
"""

import os
import sys
from pathlib import Path

# Compatibilidad de codificación para consola en Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Asegurar que el directorio raíz esté en sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database import SessionLocal, Base, engine
from app.models import Usuario, Producto
from app.core.security import hash_password

# Catálogo base de demostración asociado a los archivos estáticos de /demo
DEMO_PRODUCTOS_CONFIG = [
    {
        "nombre": "Remera de Compresión Manga Larga",
        "archivo": "remera_manga_larga.jpg",
        "precio_final": 28500.0,
        "cuotas_cantidad": 3,
        "cuotas_valor": 9500.0,
        "garantia_meses": 6,
        "stock": 25,
        "descripcion": "Remera técnica de compresión graduada con tejido transpirable Dry-Fit y costuras planas anti-rozaduras.",
    },
    {
        "nombre": "Calza Térmica de Compresión Gym",
        "archivo": "calza_termica.jpg",
        "precio_final": 34000.0,
        "cuotas_cantidad": 6,
        "cuotas_valor": 5666.0,
        "garantia_meses": 6,
        "stock": 18,
        "descripcion": "Calza larga deportiva con ajuste compresivo ergonómico de 4 vías, cintura elástica de tiro alto reforzada y bolsillo oculto.",
    },
    {
        "nombre": "Top Deportivo High-Fit",
        "archivo": "top_deportivo.jpg",
        "precio_final": 21900.0,
        "cuotas_cantidad": 3,
        "cuotas_valor": 7300.0,
        "garantia_meses": 6,
        "stock": 30,
        "descripcion": "Top compresivo de soporte alto con almohadillas termoformadas removibles y panel dorsal de malla transpirable.",
    },
    {
        "nombre": "Short Compresivo Performance",
        "archivo": "short_compresivo.jpg",
        "precio_final": 19500.0,
        "cuotas_cantidad": 3,
        "cuotas_valor": 6500.0,
        "garantia_meses": 6,
        "stock": 22,
        "descripcion": "Short doble propósito con forro interior compresivo antiroce y pantalón exterior ultra ligero microperforado.",
    },
    {
        "nombre": "Remera Manga Corta Armor",
        "archivo": "remera_manga_corta.jpg",
        "precio_final": 24000.0,
        "cuotas_cantidad": 3,
        "cuotas_valor": 8000.0,
        "garantia_meses": 6,
        "stock": 20,
        "descripcion": "Camiseta técnica de compresión muscular liviana, secado instantáneo y ventilación optimizada.",
    },
    {
        "nombre": "Sombra/Camiseta Térmica Segunda Piel",
        "archivo": "segunda_piel.jpg",
        "precio_final": 31200.0,
        "cuotas_cantidad": 6,
        "cuotas_valor": 5200.0,
        "garantia_meses": 12,
        "stock": 15,
        "descripcion": "Camiseta térmica ultra elástica efecto segunda piel con micropolar interior para mantener temperatura en exteriores.",
    },
]


def seed():
    # Asegurar existencia de tablas
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Administrador desde variables de entorno
        admin_email = os.environ.get("SEED_ADMIN_EMAIL")
        admin_password = os.environ.get("SEED_ADMIN_PASSWORD")

        if admin_email and admin_password:
            admin_existente = db.query(Usuario).filter(Usuario.email == admin_email).first()
            if not admin_existente:
                nuevo_admin = Usuario(
                    nombre="Administrador",
                    email=admin_email,
                    password_hash=hash_password(admin_password),
                    rol="admin",
                    is_admin=True,
                    activo=True,
                    acepto_tratamiento=True,
                    acepta_politica_privacidad=True,
                )
                db.add(nuevo_admin)

        # 2. Productos de demostración vinculados a /demo/<nombre_del_archivo>
        demo_dir = BASE_DIR / "app" / "static" / "demo"
        archivos_en_demo = []
        if demo_dir.exists() and demo_dir.is_dir():
            archivos_en_demo = [
                f.name for f in demo_dir.iterdir()
                if f.is_file() and not f.name.startswith(".")
            ]

        # Si hay archivos en app/static/demo, usamos esos archivos
        if archivos_en_demo:
            for archivo_nombre in archivos_en_demo:
                # Buscar si coincide con alguno de la configuración por nombre de archivo
                config = next((p for p in DEMO_PRODUCTOS_CONFIG if p["archivo"] == archivo_nombre), None)
                if config:
                    prod_nombre = config["nombre"]
                    prod_desc = config["descripcion"]
                    precio = config["precio_final"]
                    cuotas_c = config["cuotas_cantidad"]
                    cuotas_v = config["cuotas_valor"]
                    garantia = config["garantia_meses"]
                    stock = config["stock"]
                else:
                    # Nombre amigable a partir del nombre del archivo si es desconocido
                    prod_nombre = Path(archivo_nombre).stem.replace("_", " ").replace("-", " ").title()
                    prod_desc = f"Producto de demostración: {prod_nombre}"
                    precio = 10000.0
                    cuotas_c = 1
                    cuotas_v = None
                    garantia = 12
                    stock = 10

                producto_existente = db.query(Producto).filter(Producto.nombre == prod_nombre).first()
                if not producto_existente:
                    nuevo_prod = Producto(
                        nombre=prod_nombre,
                        descripcion=prod_desc,
                        imagen_url=f"/demo/{archivo_nombre}",
                        precio_final=precio,
                        cuotas_cantidad=cuotas_c,
                        cuotas_valor=cuotas_v,
                        garantia_meses=garantia,
                        stock=stock,
                    )
                    db.add(nuevo_prod)
        else:
            # Si aún no se copiaron físicamente imágenes en app/static/demo,
            # sembramos el catálogo predeterminado apuntando a /demo/<nombre_del_archivo>
            for prod_data in DEMO_PRODUCTOS_CONFIG:
                prod_nombre = prod_data["nombre"]
                producto_existente = db.query(Producto).filter(Producto.nombre == prod_nombre).first()
                if not producto_existente:
                    nuevo_prod = Producto(
                        nombre=prod_nombre,
                        descripcion=prod_data["descripcion"],
                        imagen_url=f"/demo/{prod_data['archivo']}",
                        precio_final=prod_data["precio_final"],
                        cuotas_cantidad=prod_data["cuotas_cantidad"],
                        cuotas_valor=prod_data["cuotas_valor"],
                        garantia_meses=prod_data["garantia_meses"],
                        stock=prod_data["stock"],
                    )
                    db.add(nuevo_prod)

        db.commit()
        print("Seed listo.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()


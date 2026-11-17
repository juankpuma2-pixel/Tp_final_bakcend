"""
Script de Inicialización y Semillero (SQLite tienda.db + Administrador + Catálogo)
===================================================================================
Este script realiza las siguientes tareas:
1. Conecta con la base de datos local SQLite (tienda.db) y garantiza el esquema de tablas.
2. Migra/añade automáticamente las columnas 'descripcion' e 'imagen_url' en la tabla 'productos' si no existen.
3. Registra o actualiza el usuario Administrador con las credenciales oficiales:
   - Email: juancapuma@iresm.edu.ar
   - Contraseña: Family12.
   - Permisos: is_admin = True, rol = "admin"
4. Genera el catálogo oficial con los 6 productos de ropa de compresión deportiva:
   - Precios, cuotas, garantía, stock
   - Descripciones técnicas detalladas
   - URLs de imágenes de alta calidad de Unsplash
"""

import sys
import os
from datetime import datetime, timezone
import sqlite3

# Compatibilidad de codificación para consola en Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Asegurar que la raíz del backend esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, engine, SessionLocal, SQLALCHEMY_DATABASE_URL
from app.models import Usuario, Producto
from app.core.security import hash_password, verificar_password


PRODUCTOS_COMPRESION = [
    {
        "nombre": "Remera de Compresión Manga Larga",
        "precio_final": 28500.0,
        "cuotas_cantidad": 3,
        "cuotas_valor": 9500.0,
        "garantia_meses": 6,
        "stock": 25,
        "descripcion": "Remera técnica de compresión graduada con tejido transpirable Dry-Fit y costuras planas anti-rozaduras. Optimiza el flujo sanguíneo y protege la musculatura en entrenamientos de alta intensidad.",
        "imagen_url": "https://images.unsplash.com/photo-1581655353564-df123a1eb820?w=800&auto=format&fit=crop&q=80",
    },
    {
        "nombre": "Calza Térmica de Compresión Gym",
        "precio_final": 34000.0,
        "cuotas_cantidad": 6,
        "cuotas_valor": 5666.0,
        "garantia_meses": 6,
        "stock": 18,
        "descripcion": "Calza larga deportiva con ajuste compresivo ergonómico de 4 vías, cintura elástica de tiro alto reforzada y bolsillo oculto. Reduce la vibración muscular y la fatiga post-entreno.",
        "imagen_url": "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=800&auto=format&fit=crop&q=80",
    },
    {
        "nombre": "Top Deportivo High-Fit",
        "precio_final": 21900.0,
        "cuotas_cantidad": 3,
        "cuotas_valor": 7300.0,
        "garantia_meses": 6,
        "stock": 30,
        "descripcion": "Top compresivo de soporte alto con almohadillas termoformadas removibles y panel dorsal de malla transpirable. Máxima sujeción para crossfit, running y entrenamientos funcionales.",
        "imagen_url": "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=800&auto=format&fit=crop&q=80",
    },
    {
        "nombre": "Short Compresivo Performance",
        "precio_final": 19500.0,
        "cuotas_cantidad": 3,
        "cuotas_valor": 6500.0,
        "garantia_meses": 6,
        "stock": 22,
        "descripcion": "Short doble propósito con forro interior compresivo antiroce y pantalón exterior ultra ligero microperforado. Incluye cordón interno de ajuste y bolsillo para celular seguro.",
        "imagen_url": "https://images.unsplash.com/photo-1591195853828-11db59a44f6b?w=800&auto=format&fit=crop&q=80",
    },
    {
        "nombre": "Remera Manga Corta Armor",
        "precio_final": 24000.0,
        "cuotas_cantidad": 3,
        "cuotas_valor": 8000.0,
        "garantia_meses": 6,
        "stock": 20,
        "descripcion": "Camiseta técnica de compresión muscular liviana. Fabricada con poliamida y elastano de secado instantáneo que mantiene el cuerpo fresco y seco durante toda la sesión.",
        "imagen_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&auto=format&fit=crop&q=80",
    },
    {
        "nombre": "Sombra/Camiseta Térmica Segunda Piel",
        "precio_final": 31200.0,
        "cuotas_cantidad": 6,
        "cuotas_valor": 5200.0,
        "garantia_meses": 12,
        "stock": 15,
        "descripcion": "Camiseta térmica ultra elástica efecto segunda piel con micropolar interior térmico. Diseñada para aislar las bajas temperaturas y mantener una temperatura corporal óptima en exteriores.",
        "imagen_url": "https://images.unsplash.com/photo-1578768079052-aa76e520028b?w=800&auto=format&fit=crop&q=80",
    },
]


def asegurar_columnas_sqlite():
    """Garantiza que la tabla 'productos' en SQLite tenga las columnas descripcion e imagen_url."""
    if not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        return

    db_file = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    if not os.path.exists(db_file):
        return

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(productos);")
        columnas = [col[1] for col in cursor.fetchall()]

        if columnas and "descripcion" not in columnas:
            print("      [MIGRACION] Agregando columna 'descripcion' a la tabla 'productos'...")
            cursor.execute("ALTER TABLE productos ADD COLUMN descripcion VARCHAR;")

        if columnas and "imagen_url" not in columnas:
            print("      [MIGRACION] Agregando columna 'imagen_url' a la tabla 'productos'...")
            cursor.execute("ALTER TABLE productos ADD COLUMN imagen_url VARCHAR;")

        conn.commit()
    except Exception as e:
        print(f"      [AVISO MIGRACION] {e}")
    finally:
        conn.close()


def inicializar_sistema():
    print("=" * 70)
    print("  INICIALIZACION Y SEMILLADO DE BASE DE DATOS (tienda.db)")
    print("=" * 70)

    # 1. Crear tablas si no existen
    print(f"[1/4] Verificando tablas en base de datos: {SQLALCHEMY_DATABASE_URL}...")
    Base.metadata.create_all(bind=engine)
    asegurar_columnas_sqlite()
    print("      [OK] Esquema de base de datos verificado.")

    db = SessionLocal()
    try:
        # 2. Registrar o Actualizar Administrador
        print("[2/4] Verificando usuario Administrador oficial...")
        admin_email = "juancapuma@iresm.edu.ar"
        admin_pass_plana = "Family12."
        admin_nombre = "Profesor Juan Puma"

        admin = db.query(Usuario).filter(Usuario.email == admin_email).first()
        pass_hash = hash_password(admin_pass_plana)

        if admin:
            print(f"      [INFO] Administrador '{admin_email}' ya existe (ID: {admin.id}). Actualizando permisos...")
            admin.nombre = admin_nombre
            admin.password_hash = pass_hash
            admin.rol = "admin"
            admin.is_admin = True
            admin.activo = True
            admin.acepto_tratamiento = True
            admin.acepta_politica_privacidad = True
            if not admin.fecha_consentimiento:
                admin.fecha_consentimiento = datetime.now(timezone.utc)
            admin.fecha_baja = None
            db.commit()
            db.refresh(admin)
            print(f"      [OK] Administrador actualizado exitosamente con ID: {admin.id}.")
        else:
            print(f"      [INFO] Creando nuevo Administrador '{admin_email}'...")
            nuevo_admin = Usuario(
                nombre=admin_nombre,
                email=admin_email,
                password_hash=pass_hash,
                rol="admin",
                is_admin=True,
                activo=True,
                acepto_tratamiento=True,
                acepta_politica_privacidad=True,
                fecha_consentimiento=datetime.now(timezone.utc),
            )
            db.add(nuevo_admin)
            db.commit()
            db.refresh(nuevo_admin)
            admin = nuevo_admin
            print(f"      [OK] Administrador creado exitosamente con ID: {admin.id}.")

        # 3. Semillero de Ropa Deportiva Compresiva
        print("[3/4] Sembrando catálogo oficial de ropa de compresión deportiva...")
        
        # Si los productos actuales no tienen imágenes o descripciones, los limpiamos
        productos_actuales = db.query(Producto).all()
        requiere_reemplazo = any(not p.imagen_url or not p.descripcion for p in productos_actuales) or len(productos_actuales) == 0

        if requiere_reemplazo:
            print("      [INFO] Reemplazando productos incompletos o vacíos por el catálogo deportivo...")
            db.query(Producto).delete()
            db.commit()

            for item in PRODUCTOS_COMPRESION:
                db.add(Producto(
                    nombre=item["nombre"],
                    precio_final=item["precio_final"],
                    cuotas_cantidad=item["cuotas_cantidad"],
                    cuotas_valor=item["cuotas_valor"],
                    garantia_meses=item["garantia_meses"],
                    stock=item["stock"],
                    descripcion=item["descripcion"],
                    imagen_url=item["imagen_url"],
                ))
            db.commit()
            print(f"      [OK] Insertados {len(PRODUCTOS_COMPRESION)} productos deportivos con éxito.")
        else:
            print(f"      [INFO] El catálogo ya cuenta con {len(productos_actuales)} productos completos.")

        # 4. Validar consulta de productos
        print("[4/4] Validando consulta al catálogo...")
        catalogo = db.query(Producto).all()
        for idx, prod in enumerate(catalogo, 1):
            print(f"      {idx}. [ID {prod.id}] {prod.nombre} - ${prod.precio_final:,.2f} (Stock: {prod.stock})")
            print(f"         Img: {prod.imagen_url[:50]}...")

        print("=" * 70)
        print("SISTEMA LISTO:")
        print(f"  * Base de datos:  tienda.db")
        print(f"  * Administrador:  {admin_email} | Password: {admin_pass_plana}")
        print(f"  * Total items:    {len(catalogo)} productos disponibles en catálogo")
        print("=" * 70)

    except Exception as exc:
        db.rollback()
        print(f"\n[ERROR] Falla durante la inicialización: {exc}")
        raise exc
    finally:
        db.close()


if __name__ == "__main__":
    inicializar_sistema()

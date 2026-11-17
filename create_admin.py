"""
Script de Gestión de Administrador para FastAPI + SQLAlchemy
============================================================
Este script permite registrar o actualizar un usuario con permisos
totales de Administrador (is_admin = True, rol = "admin").

Credenciales por defecto:
- Email: juancapuma@iresm.edu.ar
- Contraseña: Family12.

Uso:
    python create_admin.py
"""

import sys
import os
from datetime import datetime, timezone

# Compatibilidad de codificación para consola en Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Asegurar que el directorio raíz del proyecto esté en el PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, engine, SessionLocal
from app.models import Usuario
from app.core.security import hash_password, verificar_password


def crear_o_actualizar_admin(
    email: str = "juancapuma@iresm.edu.ar",
    password_plana: str = "Family12.",
    nombre: str = "Profesor Juan Puma"
):
    print("=" * 65)
    print("  GESTION DE USUARIO ADMINISTRADOR - FASTAPI & SQLALCHEMY")
    print("=" * 65)

    # 1. Asegurar existencia de las tablas en la BD configurada
    print("[1/3] Verificando esquema de tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("      [OK] Tablas verificadas exitosamente.")

    # 2. Iniciar sesión de SQLAlchemy
    db = SessionLocal()
    try:
        print(f"[2/3] Buscando usuario con email: '{email}'...")
        admin = db.query(Usuario).filter(Usuario.email == email).first()

        # Generar hash seguro con bcrypt
        password_hasheada = hash_password(password_plana)

        if admin:
            # Caso 1: El usuario ya existe -> Actualizar permisos y contraseña
            print(f"      [INFO] Usuario existente encontrado (ID: {admin.id}).")
            print("      [INFO] Actualizando credenciales y permisos a Administrador...")
            admin.nombre = nombre
            admin.password_hash = password_hasheada
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
            print(f"      [OK] Usuario ID {admin.id} actualizado a ADMINISTRADOR.")
        else:
            # Caso 2: El usuario no existe -> Crear nuevo administrador
            print(f"      [INFO] El usuario '{email}' no existe. Creando nuevo registro...")
            nuevo_admin = Usuario(
                nombre=nombre,
                email=email,
                password_hash=password_hasheada,
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
            print(f"      [OK] Administrador creado exitosamente con ID {admin.id}.")

        # 3. Validación de integridad de contraseña con verificar_password
        print("[3/3] Validando integridad de autenticacion...")
        valido = verificar_password(password_plana, admin.password_hash)
        if valido:
            print("      [OK] Verificacion de hash bcrypt: CORRECTA.")
        else:
            print("      [AVISO] La verificacion de contrasena devolvio False.")

        print("=" * 65)
        print("ESTADO FINAL DEL ADMINISTRADOR:")
        print(f"  * ID:         {admin.id}")
        print(f"  * Nombre:     {admin.nombre}")
        print(f"  * Email:      {admin.email}")
        print(f"  * Rol:        {admin.rol}")
        print(f"  * Is Admin:   {admin.is_admin}")
        print(f"  * Activo:     {admin.activo}")
        print(f"  * Password:   {password_plana}")
        print("=" * 65)
        return admin

    except Exception as exc:
        db.rollback()
        print(f"\n[ERROR] Ocurrio una excepcion durante la operacion: {exc}")
        raise exc
    finally:
        db.close()


if __name__ == "__main__":
    crear_o_actualizar_admin()

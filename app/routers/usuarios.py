import json
import secrets
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Depends, Response, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Usuario, Pedido, SolicitudRevocacion
from app.schemas import UsuarioCreate, UsuarioOut

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def construir_datos_usuario(db: Session, usuario: Usuario) -> Dict[str, Any]:
    pedidos_db = db.query(Pedido).filter(Pedido.usuario_id == usuario.id).all()
    pedidos_lista = []
    for p in pedidos_db:
        pedidos_lista.append({
            "id": p.id,
            "total": p.total,
            "estado": p.estado,
            "creado_en": p.creado_en,
            "items": [
                {
                    "producto_id": item.producto_id,
                    "cantidad": item.cantidad,
                    "precio_unitario": item.precio_unitario
                } for item in p.items
            ]
        })

    revocaciones_db = db.query(SolicitudRevocacion).filter(SolicitudRevocacion.usuario_id == usuario.id).all()
    revocaciones_lista = [
        {
            "codigo": r.codigo,
            "pedido_id": r.pedido_id,
            "creada_en": r.creada_en
        } for r in revocaciones_db
    ]

    return {
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "email": usuario.email,
            "rol": usuario.rol,
            "is_admin": bool(getattr(usuario, "is_admin", False) or usuario.rol == "admin"),
            "activo": usuario.activo,
            "creado_en": getattr(usuario, "creado_en", getattr(usuario, "fecha_consentimiento", None))
        },
        "pedidos": pedidos_lista,
        "solicitudes_revocacion": revocaciones_lista
    }


@router.get("/me/datos")
def obtener_mis_datos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return construir_datos_usuario(db, current_user)


@router.get("/me/exportar")
def exportar_mis_datos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    datos = construir_datos_usuario(db, current_user)
    contenido_json = json.dumps(datos, indent=4, default=str)
    return Response(
        content=contenido_json,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=mis_datos_usuario_{current_user.id}.json"}
    )


@router.delete("/me", status_code=status.HTTP_200_OK)
def dar_de_baja_cuenta(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        fecha_actual = datetime.now(timezone.utc)
        current_user = db.merge(current_user)
        current_user.activo = False
        if hasattr(current_user, "fecha_baja"):
            current_user.fecha_baja = fecha_actual

        token = secrets.token_hex(4)
        current_user.nombre = f"Usuario Anónimo {token}"
        current_user.email = f"baja_{token}_{current_user.id}@eliminado.com"
        current_user.password_hash = "CUENTA_DESACTIVADA"
        current_user.is_admin = False

        db.commit()
        return {
            "mensaje": "Cuenta dada de baja y datos anonimizados exitosamente.",
            "id": current_user.id,
            "fecha_baja": getattr(current_user, "fecha_baja", fecha_actual)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la baja: {str(e)}"
        )


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def registrar_usuario_usuarios(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    from app.routers.auth import registrar_usuario
    return registrar_usuario(usuario=usuario, db=db)


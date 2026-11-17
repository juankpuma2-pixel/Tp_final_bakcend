from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models import Pedido, Producto, Usuario
from app.schemas import PedidoCreate, PedidoEstadoUpdate, PedidoOut
from app.services.pedidos import crear_pedido, revocar_pedido_service

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

ESTADOS_VALIDOS = {"entregado", "cancelado", "procesando"}


@router.post("/", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
def checkout(
    datos: PedidoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return crear_pedido(db, current_user, datos)


# IMPORTANTE: declara rutas estáticas antes que /{pedido_id}
@router.get("/mios", response_model=List[PedidoOut])
def obtener_mis_pedidos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(Pedido).filter(
        Pedido.usuario_id == current_user.id
    ).order_by(Pedido.creado_en.desc()).all()


# ---------------------------------------------------------------------------
# GET /pedidos/admin/todos — Listar todos los pedidos (solo Admin)
# ---------------------------------------------------------------------------
@router.get("/admin/todos", response_model=List[PedidoOut])
def obtener_todos_los_pedidos_admin(
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """
    Obtiene la lista completa de todos los pedidos de la tienda.
    Exclusivo para usuarios administradores (is_admin == True).
    """
    try:
        return db.query(Pedido).order_by(Pedido.creado_en.desc()).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener los pedidos: {str(e)}"
        )


@router.get("/{pedido_id}", response_model=PedidoOut)
def obtener_pedido_por_id(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    
    is_admin = bool(getattr(current_user, "is_admin", False) or current_user.rol == "admin")
    if not pedido or (pedido.usuario_id != current_user.id and not is_admin):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    return pedido


# ---------------------------------------------------------------------------
# PATCH /pedidos/{id}/estado — Modificar estado de pedido (solo Admin)
# ---------------------------------------------------------------------------
@router.patch("/{id}/estado", response_model=PedidoOut)
@router.patch("/{id}/estado/", response_model=PedidoOut, include_in_schema=False)
def cambiar_estado_pedido(
    id: int,
    datos: PedidoEstadoUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """
    Permite al admin cambiar el estado del pedido a 'entregado', 'cancelado' o 'procesando'.
    Si se cancela un pedido, devuelve automáticamente la cantidad de prendas compradas al stock del producto.
    """
    estado_normalizado = datos.estado.strip().lower()
    if estado_normalizado not in ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado inválido. Los estados permitidos son: 'entregado', 'cancelado' o 'procesando'"
        )

    pedido = db.query(Pedido).filter(Pedido.id == id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido con ID {id} no encontrado"
        )

    try:
        # Si se cancela el pedido y no estaba cancelado previamente, devolver prendas al stock
        if estado_normalizado == "cancelado" and pedido.estado != "cancelado":
            for item in pedido.items:
                producto = db.query(Producto).filter(Producto.id == item.producto_id).first()
                if producto:
                    producto.stock += item.cantidad

        pedido.estado = estado_normalizado
        db.commit()
        db.refresh(pedido)
        return pedido
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el estado del pedido: {str(e)}"
        )


@router.post("/{pedido_id}/revocacion", status_code=status.HTTP_201_CREATED)
def revocar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    solicitud = revocar_pedido_service(db, current_user, pedido_id)
    return {
        "codigo": solicitud.codigo,
        "pedido_id": solicitud.pedido_id,
        "creada_en": solicitud.creada_en
    }
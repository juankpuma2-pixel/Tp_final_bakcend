from sqlalchemy.orm import Session
from app.models import Producto, ItemPedido
from app.schemas import ProductoCreate, ProductoOut


def crear_producto(db: Session, producto: ProductoCreate) -> Producto:
    """
    Crea un nuevo producto en la BD.
    Realiza db.commit() + db.refresh() explícito para garantizar que
    el registro se persiste a disco y que el objeto devuelto tiene el ID asignado.
    """
    db_producto = Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()               # escribe a tienda.db inmediatamente
    db.refresh(db_producto)   # recarga el objeto con los datos de la BD (incluye id, defaults)
    return db_producto


def listar_productos(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    nombre: str = None,
    precio_max: float = None,
) -> list[Producto]:
    """
    Lista productos con paginación y filtros opcionales.
    """
    try:
        skip_val = int(skip)
    except (TypeError, ValueError):
        skip_val = 0
    try:
        limit_val = int(limit)
    except (TypeError, ValueError):
        limit_val = 50

    query = db.query(Producto)

    if nombre:
        query = query.filter(Producto.nombre.ilike(f"%{nombre}%"))
    if precio_max is not None:
        query = query.filter(Producto.precio_final <= precio_max)

    return query.offset(skip_val).limit(limit_val).all()


def actualizar_producto(db: Session, producto_id: int, datos: ProductoCreate) -> Producto | None:
    """
    Actualiza un producto existente por su ID.
    Aplica db.commit() + db.refresh() explícito para que DBeaver
    vea los cambios al instante.
    """
    db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not db_producto:
        return None

    # Actualiza solo los campos que vienen en el payload (excluye None para campos opcionales)
    for campo, valor in datos.model_dump(exclude_unset=False).items():
        if valor is not None or campo in ("descripcion", "imagen_url"):
            setattr(db_producto, campo, valor)

    db.commit()               # escribe a tienda.db inmediatamente
    db.refresh(db_producto)   # recarga el objeto con los datos actualizados de la BD
    return db_producto


def eliminar_producto(db: Session, producto_id: int) -> Producto | None:
    """
    Elimina un producto y sus items de pedido asociados.
    Realiza db.commit() explícito para que la eliminación se persista a disco.
    """
    db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not db_producto:
        return None

    # Eliminar primero los items de pedido para respetar la FK
    db.query(ItemPedido).filter(
        ItemPedido.producto_id == producto_id
    ).delete(synchronize_session=False)

    db.delete(db_producto)
    db.commit()   # escribe a tienda.db inmediatamente
    return db_producto


def actualizar_stock(db: Session, producto_id: int, nuevo_stock: int) -> Producto | None:
    """
    Actualiza la cantidad disponible de stock de un producto específico.
    Aplica db.commit() + db.refresh() para persistencia inmediata en tienda.db.
    """
    try:
        db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
        if not db_producto:
            return None

        db_producto.stock = nuevo_stock
        db.commit()
        db.refresh(db_producto)
        return db_producto
    except Exception:
        db.rollback()
        raise


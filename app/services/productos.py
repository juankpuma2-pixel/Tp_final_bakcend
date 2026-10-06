from sqlalchemy.orm import Session
from app.models import Producto
from app.schemas import ProductoCreate

def crear_producto(db: Session, producto: ProductoCreate):
    db_producto = Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

def listar_productos(db: Session, skip: int = 0, limit: int = 10, nombre: str = None, precio_max: float = None):
    try:
        skip_val = int(skip)
    except (TypeError, ValueError):
        skip_val = 0
    try:
        limit_val = int(limit)
    except (TypeError, ValueError):
        limit_val = 10

    query = db.query(Producto)
    
    if nombre:
        query = query.filter(Producto.nombre.ilike(f"%{nombre}%"))
    if precio_max is not None:
        query = query.filter(Producto.precio_final <= precio_max)
        
    return query.offset(skip_val).limit(limit_val).all()
import os
import secrets
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_admin
from app.models import Producto, Usuario
from app import schemas
from app.services import productos as productos_service
from app.utils.archivos import parece_imagen

router = APIRouter(prefix="/productos", tags=["productos"])

# Extensiones permitidas y tamaño máximo (2 MB)
_EXTENSIONES_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp"}
_TAMANO_MAXIMO = 2 * 1024 * 1024  # 2 MB

# Directorio de destino (relativo a la raíz del proyecto)
_UPLOAD_DIR = Path("uploads") / "productos"


# ---------------------------------------------------------------------------
# POST /productos — Crear producto (solo Admin)
# ---------------------------------------------------------------------------
@router.post("", response_model=schemas.ProductoOut, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=schemas.ProductoOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def crear_producto(
    producto: schemas.ProductoCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """
    Crea un nuevo producto. Llama a db.commit() + db.refresh() en el servicio
    para garantizar escritura inmediata en tienda.db y visibilidad en DBeaver.
    """
    return productos_service.crear_producto(db=db, producto=producto)


# ---------------------------------------------------------------------------
# GET /productos — Listar productos (público)
# ---------------------------------------------------------------------------
@router.get("", response_model=List[schemas.ProductoOut])
@router.get("/", response_model=List[schemas.ProductoOut], include_in_schema=False)
def obtener_productos(
    skip: int = Query(0, ge=0, description="Registros a saltar para paginación"),
    limit: int = Query(50, ge=1, le=200, description="Máximo de productos a devolver"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre (parcial, case-insensitive)"),
    precio_max: Optional[float] = Query(None, description="Filtrar por precio máximo"),
    db: Session = Depends(get_db),
):
    """
    Devuelve la lista de productos con soporte de paginación y filtros.
    Responde con JSON válido en ambas rutas: /productos y /productos/
    """
    return productos_service.listar_productos(
        db=db, skip=skip, limit=limit, nombre=nombre, precio_max=precio_max
    )


# ---------------------------------------------------------------------------
# PUT /productos/{id} — Actualizar producto (solo Admin)
# ---------------------------------------------------------------------------
@router.put("/{producto_id}", response_model=schemas.ProductoOut, status_code=status.HTTP_200_OK)
def actualizar_producto(
    producto_id: int,
    producto: schemas.ProductoCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """
    Actualiza un producto existente por ID. Llama a db.commit() + db.refresh()
    para garantizar persistencia inmediata en tienda.db.
    """
    prod = productos_service.actualizar_producto(db=db, producto_id=producto_id, datos=producto)
    if not prod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado",
        )
    return prod


# ---------------------------------------------------------------------------
# DELETE /productos/{id} — Eliminar producto (solo Admin)
# ---------------------------------------------------------------------------
@router.delete("/{producto_id}", status_code=status.HTTP_200_OK)
def eliminar_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """
    Elimina un producto y sus items de pedido asociados. Llama a db.commit()
    para garantizar eliminación inmediata en tienda.db.
    """
    prod = productos_service.eliminar_producto(db=db, producto_id=producto_id)
    if not prod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado",
        )
    return {
        "mensaje": "Producto eliminado exitosamente de la base de datos",
        "id": producto_id,
    }


# ---------------------------------------------------------------------------
# PATCH /productos/{id}/stock — Modificar stock de producto (solo Admin)
# ---------------------------------------------------------------------------
@router.patch("/{id}/stock", response_model=schemas.ProductoOut, status_code=status.HTTP_200_OK)
@router.patch("/{id}/stock/", response_model=schemas.ProductoOut, status_code=status.HTTP_200_OK, include_in_schema=False)
def modificar_stock_producto(
    id: int,
    datos: schemas.ProductoStockUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """
    Permite al admin modificar la cantidad disponible de stock de un producto específico.
    Exclusivo para administradores (is_admin == True).
    """
    try:
        prod = productos_service.actualizar_stock(db=db, producto_id=id, nuevo_stock=datos.stock)
        if not prod:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {id} no encontrado",
            )
        return prod
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el stock del producto: {str(e)}"
        )


# ---------------------------------------------------------------------------
# POST /productos/{id}/imagen — Subida segura de imagen (solo Admin)
# ---------------------------------------------------------------------------
@router.post(
    "/{producto_id}/imagen",
    response_model=schemas.ProductoOut,
    status_code=status.HTTP_200_OK,
)
async def subir_imagen_producto(
    producto_id: int,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """
    Sube una imagen al producto indicado.
    Validaciones (en orden):
      1. Extension del nombre: .jpg, .jpeg, .png, .webp   -> HTTP 415 si falla
      2. Tamano: maximo 2 MB                              -> HTTP 413 si supera
      3. Firma real (magic bytes)                          -> HTTP 415 si falla
    Genera un nombre seguro con secrets.token_hex(8).
    Guarda el archivo en uploads/productos/ y persiste imagen_url en la BD.
    """
    # --- Verificar que el producto existe ---
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {producto_id} no encontrado",
        )

    # --- Validacion 1: Extension del nombre original ---
    nombre_original = archivo.filename or ""
    ext = os.path.splitext(nombre_original)[1].lower()
    if ext not in _EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Extension '{ext}' no permitida. "
                "Se aceptan: .jpg, .jpeg, .png, .webp"
            ),
        )

    # --- Leer el contenido completo ---
    contenido = await archivo.read()

    # --- Validacion 2: Tamano maximo (2 MB) ---
    if len(contenido) > _TAMANO_MAXIMO:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo supera el tamano maximo permitido de 2 MB.",
        )

    # --- Validacion 3: Firma real (magic bytes) ---
    if not parece_imagen(contenido):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                "El contenido del archivo no corresponde a una imagen valida "
                "(JPG, PNG o WebP)."
            ),
        )

    # --- Nombre seguro: NUNCA usar archivo.filename directamente ---
    nombre_seguro = f"{producto_id}-{secrets.token_hex(8)}{ext}"

    # --- Garantizar que el directorio existe ---
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # --- Guardar en disco ---
    ruta_fisica = _UPLOAD_DIR / nombre_seguro
    ruta_fisica.write_bytes(contenido)

    # --- Persistir la ruta relativa en la base de datos ---
    producto.imagen_url = f"/static/productos/{nombre_seguro}"
    db.commit()
    db.refresh(producto)

    return producto

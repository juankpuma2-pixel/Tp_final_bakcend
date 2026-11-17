from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# Esquemas de Productos
class ProductoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    precio_final: float = Field(..., gt=0, description="El precio debe ser mayor a 0")
    cuotas_cantidad: Optional[int] = Field(1, ge=1)
    cuotas_valor: Optional[float] = Field(None, gt=0)
    garantia_meses: Optional[int] = Field(12, ge=0)
    stock: Optional[int] = Field(0, ge=0)


class ProductoOut(ProductoCreate):
    id: int
    imagen_url: Optional[str] = None
    imagen: Optional[str] = None

    @model_validator(mode="after")
    def sync_image_fields(self):
        if not self.imagen and self.imagen_url:
            self.imagen = self.imagen_url
        elif not self.imagen_url and self.imagen:
            self.imagen_url = self.imagen
        return self

    class Config:
        from_attributes = True


# Esquemas para Autenticación y Usuarios
class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str = Field(..., min_length=6, description="La contraseña debe tener al menos 6 caracteres")
    acepta_politica_privacidad: bool = False
    acepto_tratamiento: Optional[bool] = True


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol: str
    is_admin: bool = False
    activo: bool = True
    acepta_politica_privacidad: bool = False

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Esquemas para Pedidos y Checkout
class ItemIn(BaseModel):
    producto_id: int
    cantidad: int = Field(..., gt=0, description="La cantidad debe ser mayor a 0")


class PedidoCreate(BaseModel):
    items: List[ItemIn] = Field(..., min_length=1)


class ItemOut(BaseModel):
    id: int
    producto_id: int
    cantidad: int
    precio_unitario: float

    class Config:
        from_attributes = True


class PedidoOut(BaseModel):
    id: int
    usuario_id: Optional[int] = None
    estado: str
    total: float
    creado_en: datetime
    items: List[ItemOut]

    class Config:
        from_attributes = True


# Esquemas para Acciones de Administrador
class ProductoStockUpdate(BaseModel):
    stock: int = Field(..., ge=0, description="Nueva cantidad de stock disponible")


class PedidoEstadoUpdate(BaseModel):
    estado: str = Field(..., description="Nuevo estado del pedido: 'entregado', 'cancelado' o 'procesando'")


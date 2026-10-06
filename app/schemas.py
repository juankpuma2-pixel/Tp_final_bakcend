from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# Esquemas de Productos
class ProductoCreate(BaseModel):
    nombre: str
    precio_final: float = Field(..., gt=0, description="El precio debe ser mayor a 0")
    cuotas_cantidad: Optional[int] = Field(None, ge=1)
    cuotas_valor: Optional[float] = Field(None, gt=0)
    garantia_meses: Optional[int] = Field(None, ge=0)
    stock: Optional[int] = Field(0, ge=0)


class ProductoOut(ProductoCreate):
    id: int

    class Config:
        from_attributes = True


# Esquemas para la Clase 7 (Autenticación y Usuarios)
class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str = Field(..., min_length=6, description="La contraseña debe tener al menos 6 caracteres")
    acepto_tratamiento: bool

    @field_validator("acepto_tratamiento")
    def debe_aceptar_tratamiento(cls, v):
        if not v:
            raise ValueError(
                "Debes aceptar el tratamiento de datos para registrarte."
            )
        return v


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Esquemas para la Clase 8 (Pedidos y Checkout)
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
    estado: str
    total: float
    creado_en: datetime
    items: List[ItemOut]

    class Config:
        from_attributes = True
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    imagen_url = Column(String, nullable=True)
    precio_final = Column(Float, nullable=False)
    cuotas_cantidad = Column(Integer, default=1)
    cuotas_valor = Column(Float)
    garantia_meses = Column(Integer, default=12)
    stock = Column(Integer, default=0)

    # Relación con items de pedido
    items_pedido = relationship("ItemPedido", back_populates="producto")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    rol = Column(String, default="customer", nullable=False)

    # Permisos de Administrador (compatible con SQLite 0/1)
    is_admin = Column(Boolean, default=False, server_default="0", nullable=False)

    # Campos de Consentimiento (Ley 25.326)
    acepto_tratamiento = Column(Boolean, nullable=False, default=True, server_default="1")
    acepta_politica_privacidad = Column(Boolean, nullable=False, default=False, server_default="0")
    fecha_consentimiento = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Campos de Baja y Anonimización
    activo = Column(Boolean, default=True, server_default="1", nullable=False)
    fecha_baja = Column(DateTime(timezone=True), nullable=True)

    # Relación con pedidos
    pedidos = relationship("Pedido", back_populates="usuario")


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    estado = Column(String, default="pendiente", nullable=False)
    total = Column(Float, nullable=False)
    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relaciones (con cascade para delete-orphan)
    usuario = relationship("Usuario", back_populates="pedidos")
    items = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")


class ItemPedido(Base):
    __tablename__ = "item_pedidos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)

    # Relaciones
    pedido = relationship("Pedido", back_populates="items")
    producto = relationship("Producto", back_populates="items_pedido")


class SolicitudRevocacion(Base):
    __tablename__ = "solicitudes_revocacion"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codigo = Column(String, unique=True, index=True, nullable=False)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    creada_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relaciones
    pedido = relationship("Pedido")
    usuario = relationship("Usuario")

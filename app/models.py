from datetime import datetime

from flask_appbuilder import Model
from flask_appbuilder.models.mixins import ImageColumn
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship


class Categoria(Model):
    __tablename__ = "categoria"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    imagen = Column(ImageColumn, nullable=True)
    activa = Column(Boolean, default=True, nullable=False)
    creada_en = Column(DateTime, default=datetime.now, nullable=False)
    actualizada_en = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    productos = relationship(
        "Producto",
        back_populates="categoria",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return self.nombre


class Producto(Model):
    __tablename__ = "producto"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(120), nullable=False)
    descripcion = Column(Text, nullable=True)
    precio = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    categoria_id = Column(Integer, ForeignKey("categoria.id"), nullable=False)
    imagen = Column(ImageColumn, nullable=True)
    estado = Column(Boolean, default=True, nullable=False)
    creado_en = Column(DateTime, default=datetime.now, nullable=False)
    actualizado_en = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    categoria = relationship(
        "Categoria",
        back_populates="productos"
    )

    items = relationship(
        "PedidoItem",
        back_populates="producto"
    )

    def __repr__(self):
        return f"{self.nombre} - {self.categoria.nombre if self.categoria else ''}"


class Cliente(Model):
    __tablename__ = "cliente"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(150), nullable=True, unique=False)
    telefono = Column(String(50), nullable=True)
    direccion = Column(Text, nullable=True)

    requiere_factura = Column(Boolean, default=False, nullable=False)
    nit = Column(String(30), nullable=True)
    razon_social = Column(String(150), nullable=True)

    creado_en = Column(DateTime, default=datetime.now, nullable=False)

    pedidos = relationship(
        "Pedido",
        back_populates="cliente",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return self.nombre


class Pedido(Model):
    __tablename__ = "pedido"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("cliente.id"), nullable=True)
    total = Column(Numeric(10, 2), nullable=False, default=0)
    estado = Column(String(50), nullable=False, default="pendiente")
    creado_en = Column(DateTime, default=datetime.now, nullable=False)
    entregado_en = Column(DateTime, nullable=True)

    cliente = relationship(
        "Cliente",
        back_populates="pedidos"
    )

    items = relationship(
        "PedidoItem",
        back_populates="pedido",
        cascade="all, delete-orphan"
    )

    pagos = relationship(
        "Pago",
        back_populates="pedido",
        cascade="all, delete-orphan"
    )

    facturas = relationship(
        "Factura",
        back_populates="pedido",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Pedido #{self.id} - {self.cliente.nombre if self.cliente else 'Cliente N/A'}"


class PedidoItem(Model):
    __tablename__ = "pedido_item"

    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey("pedido.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("producto.id"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    pedido = relationship(
        "Pedido",
        back_populates="items"
    )

    producto = relationship(
        "Producto",
        back_populates="items"
    )

    def __repr__(self):
        return f"{self.cantidad} x {self.producto.nombre if self.producto else ''}"


class Pago(Model):
    __tablename__ = "pago"

    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey("pedido.id"), nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    metodo = Column(String(50), nullable=False)
    estado = Column(String(50), nullable=False, default="pendiente")

    monto_recibido = Column(Numeric(10, 2), nullable=True)
    vuelto = Column(Numeric(10, 2), nullable=True)

    referencia_transaccion = Column(String(255), nullable=True)
    fecha = Column(DateTime, default=datetime.now, nullable=False)

    pedido = relationship(
        "Pedido",
        back_populates="pagos"
    )

    factura = relationship(
        "Factura",
        back_populates="pago",
        uselist=False
    )

    def __repr__(self):
        return f"Pago #{self.id} - {self.monto} ({self.metodo})"


class Factura(Model):
    __tablename__ = "factura"

    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey("pedido.id"), nullable=False)
    pago_id = Column(Integer, ForeignKey("pago.id"), nullable=True)
    cliente_id = Column(Integer, ForeignKey("cliente.id"), nullable=True)

    nit = Column(String(30), nullable=True)
    razon_social = Column(String(150), nullable=True)
    monto_total = Column(Numeric(10, 2), nullable=False, default=0)
    fecha = Column(DateTime, default=datetime.now, nullable=False)
    estado = Column(String(50), nullable=False, default="emitida")

    pedido = relationship(
        "Pedido",
        back_populates="facturas"
    )

    pago = relationship(
        "Pago",
        back_populates="factura"
    )

    cliente = relationship("Cliente")

    def __repr__(self):
        return f"Factura #{self.id} - {self.razon_social or 'Sin razón social'}"
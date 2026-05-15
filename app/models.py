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
	creada_en = Column(DateTime, default=datetime.utcnow, nullable=False)
	actualizada_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

	productos = relationship("Producto", back_populates="categoria", cascade="all, delete-orphan")

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
	creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
	actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

	categoria = relationship(
		"Categoria",
		back_populates="productos",
	)

	def __repr__(self):
		return f"{self.nombre} - {self.categoria.nombre if self.categoria else ''}"
from flask_appbuilder import BaseView, expose, has_access
from .extensions import appbuilder


class UsuariosProtegidoView(BaseView):
    route_base = "/usuarios"

    @expose("/")
    @has_access
    def index(self):
        return self.render_template(
            "acceso_protegido.html",
            title="Acceso Protegido"
        )


appbuilder.add_view_no_menu(UsuariosProtegidoView())


# Product CRUD using Flask-AppBuilder
from flask import current_app
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.upload import ImageUploadField
from flask_appbuilder.filemanager import ImageManager
from markupsafe import Markup
from .models import Producto, Categoria, Cliente, Pedido, PedidoItem

class CategoriaModelView(ModelView):
    datamodel = SQLAInterface(Categoria)
    form_extra_fields = {
        'imagen': ImageUploadField('Imagen', imagemanager=ImageManager())
    }
    formatters_columns = {
        'imagen': lambda v: Markup(f"<img src='{ImageManager().get_url(v)}' style='max-height:50px;'/>") if v else ''
    }
    label_columns = {
        "nombre": "Nombre",
        "descripcion": "Descripción",
        "imagen": "Imagen",
        "activa": "Activa",
        "creada_en": "Creada en",
        "actualizada_en": "Actualizada en"
    }
    list_columns = ["nombre", "descripcion", "imagen", "activa", "creada_en"]
    add_columns = ["nombre", "descripcion", "imagen", "activa"]
    edit_columns = add_columns
    show_columns = ["nombre", "descripcion", "imagen", "activa", "creada_en", "actualizada_en"]


class ProductoModelView(ModelView):
    datamodel = SQLAInterface(Producto)
    form_extra_fields = {
        'imagen': ImageUploadField('Imagen', imagemanager=ImageManager())
    }
    formatters_columns = {
        'imagen': lambda v: Markup(f"<img src='{ImageManager().get_url(v)}' style='max-height:50px;'/>") if v else ''
    }
    label_columns = {
        "nombre": "Nombre",
        "descripcion": "Descripción",
        "precio": "Precio",
        "stock": "Stock",
        "categoria": "Categoría",
        "imagen": "Imagen",
        "estado": "Estado",
        "creado_en": "Creado en",
        "actualizado_en": "Actualizado en"
    }
    list_columns = ["nombre", "precio", "stock", "categoria", "imagen", "estado"]
    add_columns = ["nombre", "descripcion", "precio", "stock", "categoria", "imagen", "estado"]
    edit_columns = add_columns
    show_columns = ["nombre", "descripcion", "precio", "stock", "categoria", "imagen", "estado", "creado_en", "actualizado_en"]


appbuilder.add_view(
    CategoriaModelView,
    "Categorías",
    icon="fa-list",
    category="Catálogo",
    category_icon="fa-list"
)

appbuilder.add_view(
    ProductoModelView,
    "Productos",
    icon="fa-coffee",
    category="Catálogo",
    category_icon="fa-coffee"
)


from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface


class ClienteModelView(ModelView):
    datamodel = SQLAInterface(Cliente)
    label_columns = {
        'nombre': 'Nombre',
        'email': 'Email',
        'telefono': 'Teléfono',
        'direccion': 'Dirección',
        'creado_en': 'Creado en'
    }
    list_columns = ['nombre', 'email', 'telefono', 'creado_en']
    add_columns = ['nombre', 'email', 'telefono', 'direccion']
    edit_columns = add_columns


class PedidoModelView(ModelView):
    datamodel = SQLAInterface(Pedido)
    label_columns = {
        'cliente': 'Cliente',
        'total': 'Total',
        'estado': 'Estado',
        'creado_en': 'Creado en',
        'entregado_en': 'Entregado en'
    }
    list_columns = ['id', 'cliente', 'total', 'estado', 'creado_en']
    add_columns = ['cliente', 'estado']
    edit_columns = ['cliente', 'estado', 'entregado_en']
    show_columns = ['id', 'cliente', 'total', 'estado', 'creado_en', 'entregado_en']


class PedidoItemModelView(ModelView):
    datamodel = SQLAInterface(PedidoItem)
    label_columns = {
        'pedido': 'Pedido',
        'producto': 'Producto',
        'cantidad': 'Cantidad',
        'precio_unitario': 'Precio unitario',
        'subtotal': 'Subtotal'
    }
    list_columns = ['pedido', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    add_columns = ['pedido', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    edit_columns = add_columns


appbuilder.add_view(
    ClienteModelView,
    "Clientes",
    icon="fa-users",
    category="Ventas",
    category_icon="fa-shopping-cart"
)

appbuilder.add_view(
    PedidoModelView,
    "Pedidos",
    icon="fa-list-alt",
    category="Ventas",
    category_icon="fa-shopping-cart"
)

appbuilder.add_view(
    PedidoItemModelView,
    "Líneas de Pedido",
    icon="fa-receipt",
    category="Ventas",
    category_icon="fa-shopping-cart"
)

# -----------------------------
# REPORTES
# -----------------------------
from sqlalchemy import func
from .extensions import db


class ReporteView(BaseView):
    route_base = "/reportes"

    @expose("/")
    @has_access
    def index(self):
        # Conteos
        total_productos = db.session.query(Producto).count()
        total_clientes = db.session.query(Cliente).count()
        total_pedidos = db.session.query(Pedido).count()

        # Sumatoria
        total_vendido = db.session.query(
            func.coalesce(func.sum(Pedido.total), 0)
        ).scalar()

        # Agrupación: pedidos por estado
        pedidos_por_estado = db.session.query(
            Pedido.estado,
            func.count(Pedido.id)
        ).group_by(Pedido.estado).all()

        # Agrupación: productos más vendidos
        productos_mas_vendidos = db.session.query(
            Producto.nombre,
            func.coalesce(func.sum(PedidoItem.cantidad), 0)
        ).join(
            PedidoItem,
            PedidoItem.producto_id == Producto.id
        ).group_by(
            Producto.id,
            Producto.nombre
        ).all()

        etiquetas_productos = [item[0] for item in productos_mas_vendidos]
        cantidades_productos = [int(item[1]) for item in productos_mas_vendidos]

        return self.render_template(
            "reportes.html",
            title="Reportes",
            total_productos=total_productos,
            total_clientes=total_clientes,
            total_pedidos=total_pedidos,
            total_vendido=total_vendido,
            pedidos_por_estado=pedidos_por_estado,
            productos_mas_vendidos=productos_mas_vendidos,
            etiquetas_productos=etiquetas_productos,
            cantidades_productos=cantidades_productos
        )


appbuilder.add_view_no_menu(ReporteView())

appbuilder.add_link(
    "Reportes",
    href="/reportes/",
    icon="fa-bar-chart",
    category="Reportes",
    category_icon="fa-bar-chart"
)

class GraficasView(BaseView):
    route_base = "/graficas"

    @expose("/")
    @has_access
    def index(self):
        # Gráfica 1: Productos más vendidos
        productos_mas_vendidos = db.session.query(
            Producto.nombre,
            func.coalesce(func.sum(PedidoItem.cantidad), 0)
        ).join(
            PedidoItem,
            PedidoItem.producto_id == Producto.id
        ).group_by(
            Producto.id,
            Producto.nombre
        ).all()

        etiquetas_productos = [item[0] for item in productos_mas_vendidos]
        cantidades_productos = [int(item[1]) for item in productos_mas_vendidos]

        # Gráfica 2: Pedidos por estado
        pedidos_por_estado = db.session.query(
            Pedido.estado,
            func.count(Pedido.id)
        ).group_by(Pedido.estado).all()

        etiquetas_estados = [item[0] for item in pedidos_por_estado]
        cantidades_estados = [int(item[1]) for item in pedidos_por_estado]

        return self.render_template(
            "graficas.html",
            title="Gráficas",
            etiquetas_productos=etiquetas_productos,
            cantidades_productos=cantidades_productos,
            etiquetas_estados=etiquetas_estados,
            cantidades_estados=cantidades_estados
        )


appbuilder.add_view_no_menu(GraficasView())

appbuilder.add_link(
    "Gráficas",
    href="/graficas/",
    icon="fa-pie-chart",
    category="Reportes",
    category_icon="fa-bar-chart"
)
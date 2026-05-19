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
from decimal import Decimal
from datetime import datetime
from flask import redirect, url_for
from wtforms import SelectField
from .models import Producto, Categoria, Cliente, Pedido, PedidoItem, Pago, Factura

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
        "nombre": "Nombre",
        "email": "Email",
        "telefono": "Teléfono",
        "direccion": "Dirección",
        "requiere_factura": "¿Requiere factura?",
        "nit": "NIT",
        "razon_social": "Razón social",
        "creado_en": "Creado en"
    }

    list_columns = [
        "nombre",
        "email",
        "telefono",
        "requiere_factura",
        "nit",
        "razon_social",
        "creado_en"
    ]

    add_columns = [
        "nombre",
        "email",
        "telefono",
        "direccion",
        "requiere_factura",
        "nit",
        "razon_social"
    ]

    edit_columns = add_columns

    show_columns = [
        "nombre",
        "email",
        "telefono",
        "direccion",
        "requiere_factura",
        "nit",
        "razon_social",
        "creado_en"
    ]


class PedidoModelView(ModelView):
    datamodel = SQLAInterface(Pedido)
    form_extra_fields = {
        "estado": SelectField(
            "Estado",
            choices=[
                ("pendiente", "Pendiente"),
                ("entregado", "Entregado"),
                ("cancelado", "Cancelado"),
            ]
        )
    }

    label_columns = {
        "cliente": "Cliente",
        "total": "Total",
        "estado": "Estado",
        "creado_en": "Creado en",
        "entregado_en": "Entregado en"
    }

    list_columns = [
        "id",
        "cliente",
        "total",
        "estado",
        "creado_en",
        "entregado_en"
    ]

    add_columns = [
        "cliente",
        "estado"
    ]

    edit_columns = [
        "cliente",
        "estado",
        "entregado_en"
    ]

    show_columns = [
        "id",
        "cliente",
        "total",
        "estado",
        "creado_en",
        "entregado_en",
        "items",
        "pagos"
    ]

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

    def on_model_change(self, form, model, is_created):
        # Asegurar precio_unitario y subtotal coherentes
        from .extensions import db
        if not model.precio_unitario and model.producto:
            model.precio_unitario = model.producto.precio
        model.subtotal = (model.precio_unitario or 0) * (model.cantidad or 0)

        # Persistir temporalmente y recalcular total del pedido desde la DB
        db.session.add(model)
        db.session.flush()
        pedido = model.pedido
        if pedido:
            total = db.session.query(func.coalesce(func.sum(PedidoItem.subtotal), 0)).filter(PedidoItem.pedido_id == pedido.id).scalar()
            pedido.total = total or 0
            db.session.add(pedido)

    def on_model_delete(self, model):
        # Recalcular total del pedido excluyendo la línea que se borrará
        from .extensions import db
        pedido = model.pedido
        if pedido:
            total_excl = db.session.query(func.coalesce(func.sum(PedidoItem.subtotal), 0)).filter(
                PedidoItem.pedido_id == pedido.id,
                PedidoItem.id != model.id
            ).scalar()
            pedido.total = total_excl or 0
            db.session.add(pedido)


class PagoModelView(ModelView):
    datamodel = SQLAInterface(Pago)
    form_extra_fields = {
    "metodo": SelectField(
        "Método",
        choices=[
            ("efectivo", "Efectivo"),
            ("qr", "QR"),
            ("tarjeta", "Tarjeta"),
        ]
    ),
    "estado": SelectField(
        "Estado",
        choices=[
            ("pendiente", "Pendiente"),
            ("pagado", "Pagado"),
            ("anulado", "Anulado"),
        ]
    )
}

    label_columns = {
        "pedido": "Pedido",
        "monto": "Monto",
        "metodo": "Método",
        "estado": "Estado",
        "monto_recibido": "Monto recibido",
        "vuelto": "Vuelto",
        "referencia_transaccion": "Referencia",
        "fecha": "Fecha",
        "factura": "Factura"
    }

    list_columns = [
        "pedido",
        "monto",
        "metodo",
        "estado",
        "monto_recibido",
        "vuelto",
        "fecha"
    ]

    add_columns = [
        "pedido",
        "monto",
        "metodo",
        "estado",
        "monto_recibido",
        "referencia_transaccion"
    ]

    edit_columns = add_columns

    show_columns = [
        "pedido",
        "monto",
        "metodo",
        "estado",
        "monto_recibido",
        "vuelto",
        "referencia_transaccion",
        "fecha",
        "factura"
    ]

    def on_model_change(self, form, model, is_created):
        pedido = model.pedido

        if pedido and (not model.monto or Decimal(model.monto) == Decimal("0")):
            model.monto = pedido.total or Decimal("0")

        metodo = (model.metodo or "").lower()
        estado = (model.estado or "").lower()

        monto = Decimal(model.monto or 0)

        if metodo == "efectivo":
            recibido = Decimal(model.monto_recibido or 0)

            if recibido < monto:
                raise Exception("El monto recibido no puede ser menor al monto a pagar.")

            model.vuelto = recibido - monto
        else:
            model.monto_recibido = None
            model.vuelto = None

        if estado == "pagado" and pedido:
            pedido.estado = "entregado"
            pedido.entregado_en = datetime.now()

            for item in pedido.items:
                if item.producto and item.cantidad:
                    item.producto.stock = max(
                        0,
                        (item.producto.stock or 0) - item.cantidad
                    )
                    db.session.add(item.producto)

            db.session.add(pedido)

            cliente = pedido.cliente

            if cliente and cliente.requiere_factura:
                factura_existente = db.session.query(Factura).filter_by(
                    pedido_id=pedido.id
                ).first()

                if not factura_existente:
                    factura = Factura(
                        pedido=pedido,
                        pago=model,
                        cliente=cliente,
                        nit=cliente.nit,
                        razon_social=cliente.razon_social or cliente.nombre,
                        monto_total=model.monto,
                        estado="emitida",
                        fecha=datetime.now()
                    )
                    db.session.add(factura)

        db.session.add(model)

class FacturaModelView(ModelView):
    datamodel = SQLAInterface(Factura)

    label_columns = {
        "pedido": "Pedido",
        "pago": "Pago",
        "cliente": "Cliente",
        "nit": "NIT",
        "razon_social": "Razón social",
        "monto_total": "Monto total",
        "fecha": "Fecha",
        "estado": "Estado"
    }

    list_columns = [
        "id",
        "pedido",
        "cliente",
        "nit",
        "razon_social",
        "monto_total",
        "fecha",
        "estado"
    ]

    add_columns = [
        "pedido",
        "pago",
        "cliente",
        "nit",
        "razon_social",
        "monto_total",
        "estado"
    ]

    edit_columns = add_columns

    show_columns = [
        "pedido",
        "pago",
        "cliente",
        "nit",
        "razon_social",
        "monto_total",
        "fecha",
        "estado"
    ]

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

appbuilder.add_view(
    PagoModelView,
    "Pagos",
    icon="fa-credit-card",
    category="Ventas",
    category_icon="fa-shopping-cart"
)

appbuilder.add_view(
    FacturaModelView,
    "Facturación",
    icon="fa-file-invoice",
    category="Ventas",
    category_icon="fa-shopping-cart"
)

class ImprimirFacturaView(BaseView):
    route_base = "/factura"

    @expose("/<int:factura_id>/imprimir")
    @has_access
    def imprimir(self, factura_id):
        factura = db.session.query(Factura).get(factura_id)

        if not factura:
            return "Factura no encontrada", 404

        return self.render_template(
            "factura_imprimir.html",
            factura=factura,
            title="Factura"
        )


appbuilder.add_view_no_menu(ImprimirFacturaView())

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

        # Sumatoria: usar pagos completados para reflejar ventas reales (case-insensitive)
        total_vendido = db.session.query(
            func.coalesce(func.sum(Pago.monto), 0)
        ).filter(func.lower(Pago.estado).in_(['completado', 'pagado'])).scalar()

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
        ).join(
            Pedido,
            PedidoItem.pedido_id == Pedido.id
        ).filter(
            func.lower(Pedido.estado).in_(['pagado', 'entregado'])
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
        ).join(
            Pedido,
            PedidoItem.pedido_id == Pedido.id
        ).filter(
            Pedido.estado.in_(['pagado', 'entregado'])
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
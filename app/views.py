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
from flask import jsonify, request, redirect, url_for
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.upload import ImageUploadField
from flask_appbuilder.filemanager import ImageManager
from markupsafe import Markup
from .models import Producto, Categoria, Cliente, Pedido, PedidoItem, Pago

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
    label_columns = {
        'pedido': 'Pedido',
        'monto': 'Monto',
        'metodo': 'Método',
        'estado': 'Estado',
        'referencia_transaccion': 'Referencia',
        'fecha': 'Fecha'
    }
    list_columns = ['pedido', 'monto', 'metodo', 'estado', 'fecha']
    add_columns = ['pedido', 'monto', 'metodo', 'estado', 'referencia_transaccion']
    edit_columns = add_columns
    show_columns = ['pedido', 'monto', 'metodo', 'estado', 'referencia_transaccion', 'fecha']

    def on_model_change(self, form, model, is_created):
        # Si el pago queda completado, marcar pedido y ajustar stock
        from .extensions import db
        # Autocompletar monto si no fue informado
        if model.pedido and (not model.monto or float(model.monto) == 0):
            model.monto = model.pedido.total

        prev_estado = None
        if not is_created and model.id:
            prev = db.session.query(Pago).get(model.id)
            if prev:
                prev_estado = (prev.estado or '').lower()

        new_estado = (model.estado or '').lower()
        if new_estado in ('completado', 'pagado') and prev_estado not in ('completado', 'pagado'):
            pedido = model.pedido
            if pedido:
                pedido.estado = 'pagado'
                # Reducir stock por cada item
                for item in pedido.items:
                    if item.producto and item.cantidad:
                        item.producto.stock = max(0, (item.producto.stock or 0) - item.cantidad)
                        db.session.add(item.producto)
                db.session.add(pedido)
        db.session.add(model)


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

# -----------------------------
# REPORTES
# -----------------------------
from sqlalchemy import func
from .extensions import db
from .services.openrouter_service import AIServiceError, OpenRouterService
from .services.reporte_general_service import ReporteGeneralError, ReporteGeneralService
from .services.reporte_tendencias_service import ReporteTendenciasError, ReporteTendenciasService
from .services.reporte_prediccion_service import ReportePrediccionError, ReportePrediccionService


class ReporteView(BaseView):
    route_base = "/reportes"

    @expose("/")
    @has_access
    def index(self):
        return self.render_template("reportes.html", title="Reportes")


class ReporteGeneralView(BaseView):
    route_base = "/reporte-general"

    @expose("/")
    @has_access
    def index(self):
        # Estado de datos para la UX (loading/error)
        data_estado = "ok"
        data_error = None

        # Valores por defecto para evitar ruptura de vista ante error
        total_productos = 0
        total_clientes = 0
        total_pedidos = 0
        total_vendido = 0
        pedidos_por_estado = []
        productos_mas_vendidos = []

        # Reporte 1 usando consultas directas MySQL con PyMySQL
        try:
            reporte_service = ReporteGeneralService.from_current_app()
            reporte_data = reporte_service.obtener_datos_reporte_1()
            total_productos = reporte_data["total_productos"]
            total_clientes = reporte_data["total_clientes"]
            total_pedidos = reporte_data["total_pedidos"]
            total_vendido = reporte_data["total_vendido"]
            pedidos_por_estado = reporte_data["pedidos_por_estado"]
            productos_mas_vendidos = reporte_data["productos_mas_vendidos"]
        except ReporteGeneralError as exc:
            data_estado = "error"
            data_error = str(exc)

        etiquetas_productos = [item[0] for item in productos_mas_vendidos]
        cantidades_productos = [int(item[1]) for item in productos_mas_vendidos]

        # Analisis automatico por IA (si esta configurado OpenRouter)
        ai_analisis = None
        ai_estado = "deshabilitado"
        ai_error = None
        if data_estado != "error":
            try:
                ai_service = OpenRouterService.from_current_app()
                if ai_service.is_enabled:
                    ai_analisis = ai_service.analizar_reporte_general(
                        {
                            "total_productos": total_productos,
                            "total_clientes": total_clientes,
                            "total_pedidos": total_pedidos,
                            "total_vendido": float(total_vendido or 0),
                            "pedidos_por_estado": [
                                {"estado": estado, "cantidad": int(cantidad)}
                                for estado, cantidad in pedidos_por_estado
                            ],
                            "productos_mas_vendidos": [
                                {"producto": nombre, "cantidad": int(cantidad)}
                                for nombre, cantidad in productos_mas_vendidos
                            ],
                        }
                    )
                    ai_estado = "activo"
                else:
                    ai_error = "Configura OPENROUTER_API_KEY para habilitar analisis automatico."
            except AIServiceError as exc:
                ai_estado = "error"
                ai_error = str(exc)
        else:
            ai_estado = "error"
            ai_error = "No se pudo generar analisis IA porque la carga de datos fallo."

        return self.render_template(
            "reporte_general.html",
            title="Reporte General por IA",
            total_productos=total_productos,
            total_clientes=total_clientes,
            total_pedidos=total_pedidos,
            total_vendido=total_vendido,
            pedidos_por_estado=pedidos_por_estado,
            productos_mas_vendidos=productos_mas_vendidos,
            etiquetas_productos=etiquetas_productos,
            cantidades_productos=cantidades_productos,
            data_estado=data_estado,
            data_error=data_error,
            ai_analisis=ai_analisis,
            ai_estado=ai_estado,
            ai_error=ai_error,
        )


class ReporteTendenciasView(BaseView):
    route_base = "/reporte-tendencias"

    @expose("/")
    @has_access
    def index(self):
        data_estado = "ok"
        data_error = None

        ventas_mensuales = []
        actividad_horaria = []
        clientes_frecuentes = []
        pedidos_30 = 0
        pedidos_prev_30 = 0
        ingresos_30 = 0
        ingresos_prev_30 = 0

        try:
            service = ReporteTendenciasService.from_current_app()
            data = service.obtener_datos_reporte_2()
            ventas_mensuales = data["ventas_mensuales"]
            actividad_horaria = data["actividad_horaria"]
            clientes_frecuentes = data["clientes_frecuentes"]
            pedidos_30 = data["pedidos_30"]
            pedidos_prev_30 = data["pedidos_prev_30"]
            ingresos_30 = data["ingresos_30"]
            ingresos_prev_30 = data["ingresos_prev_30"]
        except ReporteTendenciasError as exc:
            data_estado = "error"
            data_error = str(exc)

        variacion_pedidos_pct = 0.0
        if pedidos_prev_30 > 0:
            variacion_pedidos_pct = ((pedidos_30 - pedidos_prev_30) / pedidos_prev_30) * 100

        variacion_ingresos_pct = 0.0
        if ingresos_prev_30 > 0:
            variacion_ingresos_pct = ((ingresos_30 - ingresos_prev_30) / ingresos_prev_30) * 100

        ai_analisis = None
        ai_estado = "deshabilitado"
        ai_error = None
        if data_estado != "error":
            try:
                ai_service = OpenRouterService.from_current_app()
                if ai_service.is_enabled:
                    ai_analisis = ai_service.analizar_reporte_tendencias(
                        {
                            "ventas_mensuales": [
                                {"mes": mes, "ingresos": float(ingresos)}
                                for mes, ingresos in ventas_mensuales
                            ],
                            "actividad_horaria": [
                                {"hora": hora, "cantidad": int(cantidad)}
                                for hora, cantidad in actividad_horaria
                            ],
                            "clientes_frecuentes": [
                                {"cliente": cliente, "pedidos": int(pedidos)}
                                for cliente, pedidos in clientes_frecuentes
                            ],
                            "comparativa_30_dias": {
                                "pedidos_actual": pedidos_30,
                                "pedidos_previo": pedidos_prev_30,
                                "variacion_pedidos_pct": round(variacion_pedidos_pct, 2),
                                "ingresos_actual": float(ingresos_30),
                                "ingresos_previo": float(ingresos_prev_30),
                                "variacion_ingresos_pct": round(variacion_ingresos_pct, 2),
                            },
                        }
                    )
                    ai_estado = "activo"
                else:
                    ai_error = "Configura OPENROUTER_API_KEY para habilitar analisis automatico."
            except AIServiceError as exc:
                ai_estado = "error"
                ai_error = str(exc)
        else:
            ai_estado = "error"
            ai_error = "No se pudo generar analisis IA porque la carga de datos fallo."

        return self.render_template(
            "reporte_tendencias.html",
            title="Reporte Tendencias por IA",
            data_estado=data_estado,
            data_error=data_error,
            ventas_mensuales=ventas_mensuales,
            actividad_horaria=actividad_horaria,
            clientes_frecuentes=clientes_frecuentes,
            pedidos_30=pedidos_30,
            pedidos_prev_30=pedidos_prev_30,
            ingresos_30=ingresos_30,
            ingresos_prev_30=ingresos_prev_30,
            variacion_pedidos_pct=variacion_pedidos_pct,
            variacion_ingresos_pct=variacion_ingresos_pct,
            ai_analisis=ai_analisis,
            ai_estado=ai_estado,
            ai_error=ai_error,
        )


class ReportePrediccionView(BaseView):
    route_base = "/reporte-prediccion"

    @expose("/")
    @has_access
    def index(self):
        data_estado = "ok"
        data_error = None

        productos_demanda = []
        productos_riesgo = []
        categorias_top = []
        demanda_general = {"unidades_30d": 0.0, "unidades_90d": 0.0}
        cache_hit = False
        cache_age_seconds = 0

        force_refresh = str(request.args.get("refresh", "0")).lower() in ("1", "true", "yes")

        try:
            service = ReportePrediccionService.from_current_app()
            data = service.obtener_datos_reporte_3(force_refresh=force_refresh)
            productos_demanda = data["productos_demanda"]
            productos_riesgo = data["productos_riesgo"]
            categorias_top = data["categorias_top"]
            demanda_general = data["demanda_general"]
            cache_hit = bool(data.get("cache_hit", False))
            cache_age_seconds = float(data.get("cache_age_seconds", 0))
        except ReportePrediccionError as exc:
            data_estado = "error"
            data_error = str(exc)

        ai_analisis = None
        ai_estado = "deshabilitado"
        ai_error = None

        if data_estado != "error":
            try:
                ai_service = OpenRouterService.from_current_app()
                if ai_service.is_enabled:
                    ai_analisis = ai_service.analizar_reporte_prediccion(
                        {
                            "demanda_general": demanda_general,
                            "productos_top_demanda": productos_demanda[:8],
                            "productos_riesgo": productos_riesgo,
                            "categorias_top": categorias_top[:5],
                        }
                    )
                    ai_estado = "activo"
                else:
                    ai_error = "Configura OPENROUTER_API_KEY para habilitar analisis automatico."
            except AIServiceError as exc:
                ai_estado = "error"
                ai_error = str(exc)
        else:
            ai_estado = "error"
            ai_error = "No se pudo generar analisis IA porque la carga de datos fallo."

        return self.render_template(
            "reporte_prediccion.html",
            title="Reporte Predicción por IA",
            data_estado=data_estado,
            data_error=data_error,
            productos_demanda=productos_demanda,
            productos_riesgo=productos_riesgo,
            categorias_top=categorias_top,
            demanda_general=demanda_general,
            cache_hit=cache_hit,
            cache_age_seconds=cache_age_seconds,
            ai_analisis=ai_analisis,
            ai_estado=ai_estado,
            ai_error=ai_error,
        )


class IAServiceView(BaseView):
    route_base = "/ia"

    @expose("/")
    @has_access
    def index(self):
        return self.render_template("ia_prueba.html", title="Prueba IA")

    @expose("/health")
    @expose("/health/")
    @has_access
    def health(self):
        try:
            service = OpenRouterService.from_current_app()
            if not service.is_enabled:
                return jsonify({"ok": False, "message": "OPENROUTER_API_KEY no configurada"}), 400
            response = service.health_check()
            return jsonify({"ok": True, "response": response, "model": service.settings.model})
        except AIServiceError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 502


appbuilder.add_view_no_menu(ReporteView())
appbuilder.add_view_no_menu(ReporteGeneralView())
appbuilder.add_view_no_menu(ReporteTendenciasView())
appbuilder.add_view_no_menu(ReportePrediccionView())

appbuilder.add_link(
    "Reportes",
    href="/reportes/",
    icon="fa-bar-chart",
    category="Reportes",
    category_icon="fa-bar-chart"
)

appbuilder.add_link(
    "Reporte General por IA",
    href="/reporte-general/",
    icon="fa-line-chart",
    category="Reportes",
    category_icon="fa-bar-chart"
)

appbuilder.add_link(
    "Reporte Tendencias por IA",
    href="/reporte-tendencias/",
    icon="fa-area-chart",
    category="Reportes",
    category_icon="fa-bar-chart"
)

appbuilder.add_link(
    "Reporte Predicción por IA",
    href="/reporte-prediccion/",
    icon="fa-magic",
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

appbuilder.add_view_no_menu(IAServiceView())
appbuilder.add_link(
    "Prueba IA",
    href="/ia/",
    icon="fa-robot",
    category="Reportes",
    category_icon="fa-bar-chart"
)

# -----------------------------
# DASHBOARD PRINCIPAL
# -----------------------------

class DashboardView(BaseView):
    route_base = "/dashboard"

    @expose("/")
    @has_access
    def index(self):
        total_productos = db.session.query(Producto).count()
        total_clientes = db.session.query(Cliente).count()
        total_pedidos = db.session.query(Pedido).count()

        total_vendido = db.session.query(
            func.coalesce(func.sum(Pedido.total), 0)
        ).scalar()

        pedidos_por_estado = db.session.query(
            Pedido.estado,
            func.count(Pedido.id)
        ).group_by(Pedido.estado).all()

        productos_mas_vendidos = db.session.query(
            Producto.nombre,
            func.coalesce(func.sum(PedidoItem.cantidad), 0)
        ).join(
            PedidoItem,
            PedidoItem.producto_id == Producto.id
        ).group_by(
            Producto.id,
            Producto.nombre
        ).limit(5).all()

        etiquetas_productos = [item[0] for item in productos_mas_vendidos]
        cantidades_productos = [int(item[1]) for item in productos_mas_vendidos]

        etiquetas_estados = [item[0] for item in pedidos_por_estado]
        cantidades_estados = [int(item[1]) for item in pedidos_por_estado]

        return self.render_template(
            "dashboard.html",
            total_productos=total_productos,
            total_clientes=total_clientes,
            total_pedidos=total_pedidos,
            total_vendido=total_vendido,
            productos_mas_vendidos=productos_mas_vendidos,
            pedidos_por_estado=pedidos_por_estado,
            etiquetas_productos=etiquetas_productos,
            cantidades_productos=cantidades_productos,
            etiquetas_estados=etiquetas_estados,
            cantidades_estados=cantidades_estados
        )


appbuilder.add_view_no_menu(DashboardView())


# -----------------------------
# VENTAS - NUEVA VENTA
# -----------------------------

class NuevaVentaView(BaseView):
    route_base = "/ventas/nueva"

    @expose("/")
    @has_access
    def index(self):
        categorias = db.session.query(Categoria).order_by(Categoria.nombre.asc()).all()
        productos = db.session.query(Producto).order_by(Producto.nombre.asc()).all()

        return self.render_template(
            "ventas_nueva.html",
            categorias=categorias,
            productos=productos
        )


appbuilder.add_view_no_menu(NuevaVentaView())

# -----------------------------
# VENTAS - BUSCAR PEDIDO
# -----------------------------

class BuscarPedidoView(BaseView):
    route_base = "/ventas/buscar"

    @expose("/")
    @has_access
    def index(self):
        busqueda = request.args.get("q", "").strip()

        consulta = db.session.query(Pedido)

        if busqueda:
            consulta = consulta.join(Cliente, Pedido.cliente_id == Cliente.id).filter(
                db.or_(
                    Cliente.nombre.ilike(f"%{busqueda}%"),
                    Pedido.estado.ilike(f"%{busqueda}%"),
                    Pedido.id == busqueda if busqueda.isdigit() else False
                )
            )

        pedidos = consulta.order_by(Pedido.id.desc()).limit(30).all()

        return self.render_template(
            "ventas_buscar.html",
            pedidos=pedidos,
            busqueda=busqueda
        )


appbuilder.add_view_no_menu(BuscarPedidoView())
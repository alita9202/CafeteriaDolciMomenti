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
from .models import Producto, Categoria

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
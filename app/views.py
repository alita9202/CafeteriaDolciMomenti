from flask_appbuilder import BaseView, expose, has_access
from app import appbuilder


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
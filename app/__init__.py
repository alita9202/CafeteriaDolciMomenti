from flask import Flask

from .extensions import appbuilder , db


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object("config")
    
    db.init_app(app)
    with app.app_context():
        from .models import Categoria, Producto
        db.create_all()
        appbuilder.init_app(app, db.session)
        from . import views
        
    return app
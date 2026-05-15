import os

from flask_appbuilder.security.manager import (
    AUTH_REMOTE_USER,
    AUTH_DB,
    AUTH_LDAP,
    AUTH_OAUTH,
)

basedir = os.path.abspath(os.path.dirname(__file__))

# Clave secreta del proyecto
SECRET_KEY = "dolcimomenti_clave_secreta_123456789"

# Conexion a MySQL/XAMPP
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/cafeteria_dolcimomenti"

SQLALCHEMY_TRACK_MODIFICATIONS = False

# Seguridad de formularios
CSRF_ENABLED = True

# Autenticacion con usuario y contraseña en base de datos
AUTH_TYPE = AUTH_DB

# Nombre de la aplicacion
APP_NAME = "DOLCIMOMENTI"

# Idioma
BABEL_DEFAULT_LOCALE = "es"
BABEL_DEFAULT_FOLDER = "translations"

LANGUAGES = {
    "es": {"flag": "es", "name": "Spanish"},
    "en": {"flag": "gb", "name": "English"},
}

# Carpetas para imagenes y archivos
UPLOAD_FOLDER = basedir + "/app/static/uploads/"
IMG_UPLOAD_FOLDER = basedir + "/app/static/uploads/"
IMG_UPLOAD_URL = "/static/uploads/"
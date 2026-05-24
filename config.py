import os

from flask_appbuilder.security.manager import (
    AUTH_REMOTE_USER,
    AUTH_DB,
    AUTH_LDAP,
    AUTH_OAUTH,
)

basedir = os.path.abspath(os.path.dirname(__file__))


def _load_local_env(env_path: str) -> None:
    """Load KEY=VALUE pairs from a local .env file without extra dependencies."""
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            # Do not override variables already defined in the system env.
            os.environ.setdefault(key, value)


_load_local_env(os.path.join(basedir, ".env"))

# Clave secreta del proyecto
SECRET_KEY = os.getenv("SECRET_KEY", "dolcimomenti_clave_secreta_123456789")

# Conexion a MySQL/XAMPP
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SQLALCHEMY_DATABASE_URI",
    "mysql+pymysql://root:@localhost/cafeteria_dolcimomenti",
)

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

# OpenRouter (IA)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_TIMEOUT_SECONDS = int(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "20"))
OPENROUTER_MAX_RETRIES = int(os.getenv("OPENROUTER_MAX_RETRIES", "2"))
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "DolciMomenti")
OPENROUTER_APP_URL = os.getenv("OPENROUTER_APP_URL", "http://localhost:8080")
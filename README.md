**Setup**

- **Prerequisitos:**: Python 3.8+ y git. Recomendado crear un virtualenv.
- **Clonar:**: `git clone <repo-url>` y `cd CafeteriaDolciMomenti`

**Instalación**

- **Crear y activar entorno virtual:**:

```bash
python3 -m venv venv
source venv/bin/activate
```

- **Instalar dependencias:**: `pip install -r requirements.txt`

**Configuración**

- **Configurar la base de datos:**: Edita `config.py` y ajusta `SQLALCHEMY_DATABASE_URI`.
  - Ejemplo MySQL: `mysql+pymysql://usuario:password@localhost/nombre_db`
  - Ejemplo SQLite (rápido para pruebas): `sqlite:///app.db`
- **Secret y uploads:**: Asegúrate que `SECRET_KEY` está definido en `config.py` y que `UPLOAD_FOLDER` apunta a una carpeta existente (por ejemplo `app/static/uploads`). Crea la carpeta si no existe:

```bash
mkdir -p app/static/uploads
```

**Inicializar la base de datos y crear el admin**

- Primero exporta la app para comandos Flask:

```bash
export FLASK_APP=run.py
export FLASK_ENV=development
```

- Crear tablas (opcional — la app intenta crear tablas automáticamente al arrancar):

```bash
flask shell -c "from app import db; db.create_all()"
```

- Crear usuario administrador:

```bash
flask fab create-admin
```

Si prefieres usar un script directo:

```bash
./venv/bin/python - <<'PY'
import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app()
with app.app_context():
	from app import db
	db.create_all()
	print('Tablas creadas')
PY
```

**Ejecutar la aplicación**

- Iniciar la app en desarrollo:

```bash
flask run
# o
python run.py
```

Abre `http://localhost:5000` e inicia sesión con el admin creado.

**Permisos y problemas comunes**

- Si ves "Access is Denied" para las vistas `Productos` o `Categorías`, crea/actualiza los permisos para el rol Admin con este script:

```bash
./venv/bin/python - <<'PY'
import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app()
with app.app_context():
	from app import db
	from flask_appbuilder.security.sqla.models import Role
	sm = app.appbuilder.sm
	admin_role = db.session.query(Role).filter_by(name='Admin').first()
	for view in ['ProductoModelView', 'CategoriaModelView']:
		for perm in ['can_list', 'can_show', 'can_add', 'can_edit', 'can_delete']:
			pvm = sm.find_permission_view_menu(perm, view)
			if pvm:
				sm.add_permission_role(admin_role, pvm)
	db.session.commit()
	print('Permisos CRUD asignados a Admin')
PY
```

- Si faltan columnas (p. ej. `imagen`), puedes añadir la columna manualmente o ejecutar `db.create_all()` después de importar los modelos.

**Subida y visualización de imágenes**

- Verifica que `UPLOAD_FOLDER` está configurado en `config.py` y que el servidor tiene permisos de escritura.
- Asegúrate que `app/views.py` usa `ImageManager()` y que las URLs de imágenes son accesibles desde `app/static`.

**Despliegue y producción**

- Configura variables de entorno para `SECRET_KEY` y la URI de la base de datos.
- Usa un servidor WSGI (gunicorn/uWSGI) y una base de datos robusta (MySQL/Postgres) para producción.

**Comandos útiles**

- Activar entorno: `source venv/bin/activate`
- Instalar: `pip install -r requirements.txt`
- Crear admin: `flask fab create-admin`
- Ejecutar app: `flask run`

**Integración IA (OpenRouter) - Fase 1**

- Copia variables base:

```bash
cp .env.example .env
```

- Configura al menos `OPENROUTER_API_KEY`.
- Modelo recomendado para esta fase: `openai/gpt-4o-mini`.
  - Razón: buen equilibrio entre costo, latencia y calidad para análisis textual de métricas.

- Prueba básica de conectividad IA desde la app:

```bash
flask run
```

Luego abre:

- `http://localhost:5000/ia/health` (o puerto configurado)

También se integra análisis IA en:

- `Reportes` -> `Análisis automático por IA`

**Contacto**

- Si necesitas ayuda adicional, dime qué error exacto ves y lo reviso.

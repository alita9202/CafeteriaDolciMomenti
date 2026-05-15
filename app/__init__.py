from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_appbuilder import AppBuilder

app = Flask(__name__)
app.config.from_object("config")

db = SQLAlchemy(app)

with app.app_context():
    appbuilder = AppBuilder(app, db.session)

from app import views
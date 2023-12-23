from flask import Flask
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_ckeditor import CKEditor
from os import environ

app = Flask(__name__)


app.config['SECRET_KEY'] = 'Random charachter'
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking as it can cause performance issues

db = SQLAlchemy(app)


bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

ckeditor = CKEditor(app)

from texthub import routes
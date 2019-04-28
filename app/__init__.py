import quart.flask_patch
from quart_trio import QuartTrio
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap

app = QuartTrio(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
login = LoginManager(app)
login.login_view = 'login'

from app import routes, models


# db.create_all()
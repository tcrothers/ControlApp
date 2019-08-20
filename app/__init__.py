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

# hardware support
from app import mock_objs

xps1 = mock_objs.fake_xps
all_insts = mock_objs.all_insts

from app import scans
scan = scans.Scan(all_insts)

# routing
from app import routes, models, websockets

# todo: print vals to file
# todo: connect to instruments
# todo: display results

# db.create_all()
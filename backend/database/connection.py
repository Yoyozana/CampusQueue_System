from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# These are created here, unattached to any app, and then wired up to the
# real Flask app in app.py via db.init_app(app), jwt.init_app(app), etc.
# This two-step pattern (create here, attach in app.py) is what lets
# database/models.py and services/*.py import `db` directly without
# needing to import the whole app.py (which would cause circular imports).
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

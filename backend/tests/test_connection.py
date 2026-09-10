from flask import Flask
from config import Config
from database.connection import db, jwt, cors

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
jwt.init_app(app)
cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

print("PASS: extensions attached to the app with no errors")

# Now actually try connecting to YOUR real MySQL server and creating tables
# (there are no models registered yet, so this just confirms the connection
# itself works, not that any tables get created)
with app.app_context():
    db.create_all()
    print("PASS: successfully connected to your MySQL database")

import os
from flask import Flask, jsonify

from config import Config
from database.connection import db, jwt, cors
from routes.auth_routes import bp as auth_bp
from routes.queue_routes import bp as queue_bp
from routes.admin_routes import bp as admin_bp
from routes.notification_routes import bp as notification_bp

# Note: there is no separate routes/student_routes.py - student-facing
# queue actions (list queues, join, ticket status, cancel, active
# tickets) all live in routes/queue_routes.py instead, since they're
# closely related and didn't warrant a further split.


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- Extensions ---
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
                  supports_credentials=True)

    # --- Blueprints ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(queue_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notification_bp)

    # --- Health check (confirms the deployed Render service is alive) ---
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    # --- JWT error handlers: return clean JSON instead of Flask-JWT-Extended's
    # default plain-text/HTML error bodies, so the frontend always gets JSON ---
    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "Missing or invalid authorization token"}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Invalid token"}), 422

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired"}), 401

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])

import os
from flask import Flask, jsonify, send_from_directory, abort, request

from config import Config
from database.connection import db, jwt, cors
from routes.auth_routes import bp as auth_bp
from routes.queue_routes import bp as queue_bp
from routes.admin_routes import bp as admin_bp
from routes.notification_routes import bp as notification_bp
from flask_migrate import Migrate 
# Note: there is no separate routes/student_routes.py - student-facing
# queue actions (list queues, join, ticket status, cancel, active
# tickets) all live in routes/queue_routes.py instead, since they're
# closely related and didn't warrant a further split.


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- Extensions ---
    db.init_app(app)
    migrate = Migrate(app, db)
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
        
    # --- Serve the frontend from the same server (one deploy, no CORS issues) ---
    frontend_dir = os.path.abspath(os.environ.get(
        "FRONTEND_DIR", os.path.join(os.path.dirname(__file__), "..", "frontend")))

    @app.route("/")
    def home():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:filename>")
    def frontend_files(filename):
        if filename.startswith("api/"):
            abort(404)
        return send_from_directory(frontend_dir, filename)

    # --- Security headers: block cross-site scripting and clickjacking ---
    @app.after_request
    def security_headers(resp):
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; "
            "connect-src 'self' " + " ".join(app.config["CORS_ORIGINS"]) + "; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

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

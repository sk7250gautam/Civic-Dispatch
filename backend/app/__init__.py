import os
import click
from flask import Flask, jsonify, request
from config import config_by_name
from app.extensions import db, migrate, login_manager, limiter, cors, ma
from app.models.user import User

def create_app(config_name: str = None) -> Flask:
    if not config_name:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)
    allowed_origins = [
        r"http://localhost:\d+",
        r"http://127\.0\.0\.1:\d+",
        r"https://.*\.vercel\.app",
        r"https://.*\.onrender\.com"
    ]
    custom_origins = os.getenv("CORS_ORIGINS")
    if custom_origins:
        allowed_origins.extend([o.strip() for o in custom_origins.split(",") if o.strip()])

    cors.init_app(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)
    ma.init_app(app)

    # Configure User Loader
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"error": "UNAUTHORIZED", "message": "Authentication required to access this resource."}), 401

    # Register Blueprints
    from app.api.auth_routes import auth_bp
    from app.api.citizen_routes import citizen_bp
    from app.api.officer_routes import officer_bp
    from app.api.manager_routes import manager_bp
    from app.api.admin_routes import admin_bp
    from app.api.public_routes import public_bp
    from app.api.ai_routes import ai_bp
    from app.api.attachment_routes import attachment_bp
    from app.api.notification_routes import notification_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(citizen_bp)
    app.register_blueprint(officer_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(attachment_bp)
    app.register_blueprint(notification_bp)

    # Register CLI Commands
    @app.cli.command("seed-db")
    @click.option("--reset", is_flag=True, help="Drops and recreates all tables before seeding.")
    def seed_db_command(reset):
        """Populates database with realistic municipal demo data and role accounts."""
        from app.seeds.demo_data import seed_database
        seed_database(reset=reset)
        click.echo("Seed command finished successfully.")

    @app.cli.command("sla-check")
    def sla_check_command():
        """Synchronously runs SLA sweep and escalation logic."""
        from app.sla.engine import SLAEngine
        click.echo("Running manual SLA sweep...")
        results = SLAEngine.run_evaluation()
        click.echo(f"SLA Evaluation completed: {results}")

    # Standardized Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "BAD_REQUEST", "message": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "NOT_FOUND", "message": "Resource not found."}), 404

    @app.errorhandler(429)
    def ratelimit_handler(error):
        return jsonify({"error": "RATE_LIMIT_EXCEEDED", "message": "Too many requests. Please slow down."}), 429

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": "An unexpected server error occurred."}), 500

    @app.route("/", methods=["GET"])
    def index():
        if "text/html" in request.headers.get("Accept", ""):
            return """
            <!DOCTYPE html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <title>Civic Dispatch API — Live</title>
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem; display: flex; justify-content: center; align-items: center; min-height: 80vh; margin: 0; }
                .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 2.2rem; max-width: 620px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 100%; box-sizing: border-box; }
                h1 { color: #20dbc1; margin-top: 0; font-size: 1.75rem; letter-spacing: -0.025em; }
                .badge { background: #057a6d; color: #c7fdf3; padding: 4px 12px; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; display: inline-block; margin-bottom: 1.2rem; }
                p { line-height: 1.6; color: #94b3d4; font-size: 0.95rem; }
                .link { color: #51f0d7; text-decoration: none; font-weight: 600; }
                .link:hover { text-decoration: underline; }
                code { background: #0d1929; padding: 3px 8px; border-radius: 4px; color: #f59e0b; font-family: monospace; font-size: 0.88rem; }
                ul { list-style: none; padding-left: 0; margin: 1.2rem 0; }
                li { padding: 8px 0; border-bottom: 1px solid #334155; font-size: 0.92rem; display: flex; justify-content: space-between; }
                .tip { background: #0d1929; border-left: 4px solid #08bfa6; padding: 12px 16px; border-radius: 6px; margin-top: 1.5rem; font-size: 0.88rem; color: #e1e9f2; }
              </style>
            </head>
            <body>
              <div class="card">
                <span class="badge">● API LIVE & OPERATIONAL</span>
                <h1>🏛️ Civic Dispatch API</h1>
                <p>The municipal backend, finite state machine, and SLA engine are actively running on Render.</p>
                <ul>
                  <li><span>📊 Public Transparency Stats</span> <a class="link" href="/api/v1/public/stats">/api/v1/public/stats</a></li>
                  <li><span>💓 Health Check</span> <a class="link" href="/api/health">/api/health</a></li>
                  <li><span>🏢 Departments & Zones</span> <a class="link" href="/api/v1/public/departments">/api/v1/public/departments</a></li>
                  <li><span>👥 Demo Accounts</span> <a class="link" href="/api/v1/auth/demo-accounts">/api/v1/auth/demo-accounts</a></li>
                  <li><span>🐙 GitHub Repository</span> <a class="link" href="https://github.com/sk7250gautam/Civic-Dispatch" target="_blank">sk7250gautam/Civic-Dispatch</a></li>
                </ul>
                <div class="tip">
                  💡 <strong>Frontend UI:</strong> Deploy the React frontend on <strong>Vercel</strong> with <code>VITE_API_BASE_URL=https://civic-dispatch.onrender.com</code> to open the full visual portal!
                </div>
              </div>
            </body>
            </html>
            """, 200, {"Content-Type": "text/html"}
        return jsonify({
            "platform": "CIVIC DISPATCH API",
            "version": "1.0.0",
            "status": "OPERATIONAL",
            "documentation": "https://github.com/sk7250gautam/Civic-Dispatch"
        }), 200

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "civic-dispatch-api",
            "version": "1.0.0"
        }), 200

    return app

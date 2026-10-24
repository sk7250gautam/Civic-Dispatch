import os
import click
from flask import Flask, jsonify
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
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
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

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "civic-dispatch-api",
            "version": "1.0.0"
        }), 200

    return app

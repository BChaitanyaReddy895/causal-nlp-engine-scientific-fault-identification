"""
Flask application factory.
Initializes and configures the Flask app with blueprints and extensions.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import get_config


def create_app(config_name=None):
    """
    Application factory function.
    
    Args:
        config_name: Configuration environment (development, testing, production)
        
    Returns:
        Configured Flask application instance
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)

    # Setup logging
    setup_logging(app)

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints (will be created in milestone 8)
    register_blueprints(app)

    # Register CLI commands
    register_cli_commands(app)

    return app


def setup_logging(app):
    """Configure logging for the application."""
    if not app.debug:
        handler = logging.StreamHandler()
        handler.setLevel(app.config["LOG_LEVEL"])
        formatter = logging.Formatter(app.config["LOG_FORMAT"])
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.setLevel(app.config["LOG_LEVEL"])


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "error": "Bad Request",
            "message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found",
            "timestamp": datetime.utcnow().isoformat()
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {error}")
        return jsonify({
            "error": "Server Error",
            "message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }), 500


def register_blueprints(app):
    """Register Flask blueprints."""
    from backend.api.health_routes import health_bp
    from backend.api.verify_routes import verify_bp
    from backend.api.enhanced_routes import enhanced_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(verify_bp)
    app.register_blueprint(enhanced_bp)  # Advanced API with enhanced features


def register_cli_commands(app):
    """Register Flask CLI commands."""

    @app.cli.command()
    def init_db():
        """Initialize the database."""
        print("Initializing database...")
        # TODO: Add database initialization logic

    @app.cli.command()
    def load_kg():
        """Load knowledge graph."""
        print("Loading knowledge graph...")
        # TODO: Add KG loading logic


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)

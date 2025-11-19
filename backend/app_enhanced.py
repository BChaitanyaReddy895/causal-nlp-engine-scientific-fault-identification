"""Enhanced Flask application with all components."""

import logging
from flask import Flask, jsonify
from flask_cors import CORS
from pathlib import Path

# Import blueprints
from backend.api.health_routes import health_bp
from backend.api.verify_routes import verify_bp
from backend.api.advanced_routes import admin_bp, status_bp, register_advanced_routes
from backend.api.routes import extract_bp
from backend.config import get_config


def create_app(config_name='development'):
    """Create Flask application with full configuration."""
    
    # Create app
    app = Flask(__name__)
    
    # Load config
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Setup logging
    setup_logging(app)
    
    # Initialize CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(verify_bp)
    app.register_blueprint(extract_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(status_bp)
    
    # Register advanced routes
    register_advanced_routes(app)
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"Server error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
    # CLI commands
    @app.cli.command()
    def init_db():
        """Initialize database."""
        from backend.kg.kg_manager import KGManager
        kg = KGManager()
        app.logger.info("Database initialized")
    
    @app.cli.command()
    def load_kg():
        """Load knowledge graphs."""
        from backend.kg.kg_manager import setup_kg
        kg = setup_kg()
        app.logger.info("Knowledge graphs loaded")
    
    app.logger.info(f"App created with config: {config_name}")
    return app


def setup_logging(app):
    """Setup application logging."""
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    
    # Create logs directory
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Setup file handler
    file_handler = logging.FileHandler(logs_dir / 'app.log')
    file_handler.setLevel(getattr(logging, log_level))
    
    # Setup formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler
    app.logger.addHandler(file_handler)
    app.logger.setLevel(getattr(logging, log_level))


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

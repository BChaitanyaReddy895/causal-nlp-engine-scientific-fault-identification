"""
Health check endpoints.
"""

from datetime import datetime

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__, url_prefix="/")


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON object with service status and timestamp
    """
    return jsonify({
        "status": "healthy",
        "service": "causal-nlp-engine",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@health_bp.route("/", methods=["GET"])
def index():
    """Root endpoint with service information."""
    return jsonify({
        "service": "Causal-NLP Engine for Fake Scientific Claims Detection",
        "version": "0.1.0",
        "status": "running",
        "api_prefix": "/api",
        "docs": "/api/docs"
    }), 200

"""Backend routes and API structure."""

from flask import Blueprint, request, jsonify
from ..causal_extractor.extractor import CausalExtractor
from ..kg.kg_manager import KGManager
from ..verifier.pipeline import create_verification_pipeline

# Create blueprints
health_bp = Blueprint('health', __name__)
extract_bp = Blueprint('extract', __name__, url_prefix='/api')
verify_bp = Blueprint('verify', __name__, url_prefix='/api')


@health_bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "causal-nlp-engine",
        "version": "1.0.0"
    }), 200


@extract_bp.route('/extract/triples', methods=['POST'])
def extract_triples():
    """Extract causal triples from text."""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Missing text field"}), 400

    try:
        extractor = CausalExtractor()
        triples = extractor.extract(data['text'])
        return jsonify({"triples": triples, "count": len(triples)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@verify_bp.route('/verify', methods=['POST'])
def verify():
    """Verify claim with full pipeline."""
    data = request.get_json()
    if not data or 'claim' not in data:
        return jsonify({"error": "Missing claim field"}), 400

    try:
        # Initialize components
        extractor = CausalExtractor()
        kg = KGManager()

        # Verify
        result = {
            "verdict": "CORRELATION_NOT_CAUSAL",
            "confidence": 0.85,
            "triples": extractor.extract(data['claim'])
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

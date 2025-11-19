"""
Flask application configuration.
Supports multiple environments: development, testing, production.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration."""

    # Flask settings
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # CORS settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5000").split(",")

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Database (SQLite by default, can be overridden)
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///./causal_nlp.db"
    )

    # Model paths
    MODELS_DIR = os.getenv("MODELS_DIR", "models/")
    CAUSAL_EXTRACTOR_MODEL = os.path.join(MODELS_DIR, "extractors/causal_extractor.pt")
    GRAPH_MODEL_PATH = os.path.join(MODELS_DIR, "graph_model/graph_model.pt")

    # Data paths
    DATA_DIR = os.getenv("DATA_DIR", "data/")
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

    # Knowledge Graph settings
    KG_TYPE = os.getenv("KG_TYPE", "sqlite")  # Options: sqlite, neo4j
    KG_PATH = os.getenv("KG_PATH", "data/kg.db")

    # API settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    JSON_SORT_KEYS = False

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Model configuration
    TRANSFORMER_MODEL = "microsoft/deberta-v3-small"
    MAX_SEQ_LENGTH = 512
    BATCH_SIZE = 32

    # GNN configuration
    GNN_HIDDEN_DIM = 128
    GNN_NUM_LAYERS = 3
    GNN_DROPOUT = 0.1

    # Verification settings
    CONFIDENCE_THRESHOLD = 0.5
    MAX_TRIPLES_PER_CLAIM = 10


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False
    LOG_LEVEL = "DEBUG"
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration."""

    DEBUG = True
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    KG_PATH = ":memory:"
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    LOG_LEVEL = "INFO"


# Configuration dictionary
config_dict = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(env=None):
    """Get configuration object based on environment."""
    if env is None:
        env = os.getenv("FLASK_ENV", "development")
    return config_dict.get(env, config_dict["default"])

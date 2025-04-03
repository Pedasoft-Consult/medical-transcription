"""
Fixed app/__init__.py to resolve SQLAlchemy model registration issues
"""
import os
import logging

from flask import Flask, jsonify
from dotenv import load_dotenv

from .swagger import register_swagger
from .config import config
from .logging_setup import setup_logging
from .utils.error_handling import register_error_handlers
from .services.security_service import setup_security_headers, setup_cors

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Load environment variables based on environment
def load_environment_config():
    """Load environment-specific configuration"""
    env = os.environ.get("FLASK_ENV", "development")
    env_file = f".env.{env}"

    if os.path.exists(env_file):
        logger.info(f"Loading environment from {env_file}")
        load_dotenv(env_file)
    else:
        logger.info("Loading environment from default .env file")
        load_dotenv()


def create_app():
    """Create and configure the Flask application with enhanced security"""
    # Load environment variables
    load_environment_config()

    # Create the app
    app = Flask(__name__,
                static_folder=config.get_static_folder(),
                static_url_path=config.get_static_url_path())

    # Configure database first - before initializing extensions
    app.config["SQLALCHEMY_DATABASE_URI"] = config.get_db_url()
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = config.get_db_engine_options()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Debug the database configuration
    app.logger.info(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Replace secret key
    app.secret_key = config.get_secret_key()

    # Setup logging - Should come early in initialization
    setup_logging(app)

    # Initialize database
    from .db import db
    db.init_app(app)

    # Setup CORS with proper configuration
    setup_cors(app)

    # Setup security headers
    setup_security_headers(app)

    # Register error handlers
    register_error_handlers(app)

    # Create application context and import models here to avoid circular imports
    with app.app_context():
        # Import models - this should be done INSIDE the app context
        # Note: we're importing the models package once, rather than individual models
        from .models import user, transcript, translation, audit_log

        # Create database tables
        db.create_all()
        app.logger.info("Database tables created or verified")

    # Initialize rate limiter
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        from .utils.redis_compat import get_redis_storage

        # Try to use Redis storage if available
        redis_storage = None
        try:
            import redis

            RedisStorage = get_redis_storage()
            if not RedisStorage:
                raise ImportError("RedisStorage class could not be loaded")

            # Get Redis URL from config or environment
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            redis_client = redis.from_url(redis_url)

            # Test connection
            redis_client.ping()

            # Create storage
            redis_storage = RedisStorage(redis_client)
            app.logger.info("Using Redis storage for rate limiting")
        except (ImportError, Exception) as e:
            app.logger.warning(f"Could not initialize Redis storage for rate limiting: {str(e)}")
            app.logger.warning("Falling back to in-memory storage (not recommended for production)")
            redis_storage = None

        # Initialize limiter with the best available storage
        if redis_storage:
            limiter = Limiter(
                get_remote_address,
                app=app,
                storage=redis_storage,
                default_limits=["200 per day", "50 per hour"]
            )
        else:
            # Use default in-memory storage
            limiter = Limiter(
                get_remote_address,
                app=app,
                default_limits=["200 per day", "50 per hour"]
            )
            app.logger.warning("Using in-memory storage for rate limiting. NOT RECOMMENDED FOR PRODUCTION.")

        # Make limiter available for routes
        app.limiter = limiter
    except ImportError:
        app.logger.warning("Flask-Limiter not installed, rate limiting disabled")

    # Register API blueprints
    from .routes.auth import auth_bp
    from .routes.ai_transcription import ai_transcription_bp
    from .routes.ai_translation import ai_translation_bp

    # Register all routes
    try:
        app.register_blueprint(auth_bp)
        app.register_blueprint(ai_transcription_bp)
        app.register_blueprint(ai_translation_bp)
        app.logger.info("API routes registered")
    except ImportError as e:
        app.logger.warning(f"Some API routes could not be registered: {str(e)}")

    # Register audio routes
    from .services.audio_playback import register_audio_routes
    register_audio_routes(app)

    # Register monitoring routes
    try:
        from .services.monitoring import register_monitoring_routes
        register_monitoring_routes(app)
        app.logger.info("Monitoring routes registered")
    except ImportError:
        app.logger.warning("Monitoring services not available")

    # Register data retention commands
    from .services.data_retention import register_data_retention_commands
    register_data_retention_commands(app)

    # Register Swagger documentation
    register_swagger(app)

    # Serve frontend static files
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(app.static_folder + '/' + path):
            return app.send_static_file(path)
        else:
            return app.send_static_file('index.html')

    # Basic health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({"status": "healthy"})

    return app
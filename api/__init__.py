"""
Fixed app/__init__.py to resolve SQLAlchemy model registration issues
"""
import os
import logging

from flask import Flask, jsonify
from dotenv import load_dotenv

from .db import db, reset_sqlalchemy
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
    # Reset SQLAlchemy to clear any previous mappers
    reset_sqlalchemy()

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
    db.init_app(app)

    # Setup CORS with proper configuration
    setup_cors(app)

    # Setup security headers
    setup_security_headers(app)

    # Register error handlers
    register_error_handlers(app)

    # Initialize rate limiter
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address

        # Try to use Redis storage if available
        redis_storage = None
        try:
            # Get Redis client from utility
            from .utils.redis_fix import get_redis_client

            # Get Redis URL from config or environment
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            redis_client = get_redis_client(redis_url)

            if redis_client:
                # Try to get the appropriate RedisStorage class
                from .utils.redis_compat import get_redis_storage
                RedisStorage = get_redis_storage()

                if RedisStorage:
                    # Create storage with Redis client
                    try:
                        redis_storage = RedisStorage(redis_client)
                        app.logger.info("Using Redis storage for rate limiting")
                    except TypeError as e:
                        app.logger.warning(f"Redis storage initialization error: {e}")
                        # Try alternate initialization method
                        try:
                            redis_storage = RedisStorage(redis_url)
                            app.logger.info("Using Redis storage for rate limiting with URL")
                        except Exception as e:
                            app.logger.warning(f"Failed to initialize Redis storage with URL: {e}")
            else:
                app.logger.warning("Could not connect to Redis")
        except Exception as e:
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
    except Exception as e:
        app.logger.warning(f"Could not initialize rate limiting: {str(e)}")

    # Register API blueprints
    try:
        from .routes.auth import auth_bp
        app.register_blueprint(auth_bp)
        app.logger.info("Registered auth routes")
    except Exception as e:
        app.logger.error(f"Failed to register auth routes: {str(e)}")

    # Replace the transcription routes registration
    try:
        from .routes.ai_transcription import ai_transcription_bp
        app.register_blueprint(ai_transcription_bp)
        app.logger.info("Registered transcription routes")
    except Exception as e:
        app.logger.error(f"Failed to register transcription routes: {str(e)}")

    # Replace the translation routes registration
    try:
        from .routes.ai_translation import ai_translation_bp
        app.register_blueprint(ai_translation_bp)
        app.logger.info("Registered translation routes")
    except Exception as e:
        app.logger.error(f"Failed to register translation routes: {str(e)}")

    # Register audio routes
    try:
        from .services.audio_playback import register_audio_routes
        register_audio_routes(app)
        app.logger.info("Registered audio routes")
    except Exception as e:
        app.logger.error(f"Failed to register audio routes: {str(e)}")

    # Create database tables if they don't exist
    try:
        with app.app_context():
            # Create tables
            db.create_all()
            app.logger.info("Database tables created or verified")
    except Exception as e:
        app.logger.error(f"Error creating database tables: {str(e)}")

    # Register monitoring routes
    try:
        from .services.monitoring import register_monitoring_routes
        register_monitoring_routes(app)
        app.logger.info("Monitoring routes registered")
    except Exception as e:
        app.logger.warning(f"Monitoring services not available: {str(e)}")

    # Register data retention commands
    try:
        from .services.data_retention import register_data_retention_commands
        register_data_retention_commands(app)
        app.logger.info("Data retention commands registered")
    except Exception as e:
        app.logger.warning(f"Data retention services not available: {str(e)}")

    # Register Swagger documentation
    try:
        register_swagger(app)
        app.logger.info("Swagger documentation registered")
    except Exception as e:
        app.logger.warning(f"Swagger documentation not available: {str(e)}")

    # Serve frontend static files
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(app.static_folder + '/' + path):
            return app.send_static_file(path)
        else:
            return app.send_static_file('index.html')

    # Add debug endpoint to help troubleshoot deployment issues
    @app.route('/api/debug/config', methods=["GET"])
    def debug_config():
        # Only expose in development mode
        if app.debug:
            # Return sanitized configuration (removing sensitive info)
            safe_config = {
                "FLASK_ENV": os.environ.get("FLASK_ENV"),
                "FLASK_DEBUG": os.environ.get("FLASK_DEBUG"),
                "PORT": os.environ.get("PORT"),
                "DATABASE_URL_PREFIX": os.environ.get("DATABASE_URL", "")[:20] + "..." if os.environ.get(
                    "DATABASE_URL") else None,
                "PYTHON_VERSION": os.environ.get("PYTHON_VERSION"),
                "VERCEL": os.environ.get("VERCEL"),
            }
            return jsonify(safe_config)
        return jsonify({"message": "Debug information only available in debug mode"})

    # Basic health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({"status": "healthy"})

    return app
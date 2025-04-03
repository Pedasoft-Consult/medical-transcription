"""
Medical Transcription App
Main application initialization with AI services and enhanced security
"""
import os
import logging

from flask import Flask, jsonify
from flask_cors import CORS

from .swagger import register_swagger
from .config import config
from .logging_setup import setup_logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application"""
    # Create the app
    app = Flask(__name__,
                static_folder=config.get_static_folder(),
                static_url_path=config.get_static_url_path())

    # Enable CORS for all API routes with proper configuration
    CORS(app,
         resources={r"/api/*": {"origins": ["http://localhost:3000"], "supports_credentials": True}},
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "Accept"])

    # Replace secret key
    app.secret_key = config.get_secret_key()

    # Replace database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = config.get_db_url()
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = config.get_db_engine_options()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Setup logging - Should come early in initialization
    setup_logging(app)

    # Initialize extensions
    from .db import db
    db.init_app(app)

    # Initialize rate limiter with the best available storage
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    # Try to use Redis storage if available
    # Try to use Redis storage if available
    redis_storage = None
    try:
        import redis
        from flask_limiter.util import get_remote_address
        from flask_limiter.storage import RedisStorage  # Correct import path

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
            storage=redis_storage,
            default_limits=["200 per day", "50 per hour"]
        )
    else:
        # Use default in-memory storage
        limiter = Limiter(
            get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )
        app.logger.warning("Using in-memory storage for rate limiting. NOT RECOMMENDED FOR PRODUCTION.")

    limiter.init_app(app)

    # Make limiter available for routes
    app.limiter = limiter

    # Setup enhanced security
    from .services.security_service import setup_security_headers
    setup_security_headers(app)

    # Register error handlers
    register_error_handlers(app)

    # Register API blueprints
    from .routes.auth import auth_bp
    from .routes.ai_transcription import ai_transcription_bp
    from .routes.ai_translation import ai_translation_bp

    # Register AI-enhanced routes if services are available
    try:
        app.register_blueprint(auth_bp)
        app.register_blueprint(ai_transcription_bp)
        app.register_blueprint(ai_translation_bp)
        app.logger.info("AI-enhanced transcription and translation services registered")
    except ImportError as e:
        app.logger.warning(f"AI services not available: {str(e)}")
        app.logger.warning("The application will use standard transcription and translation services")

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

    # Register Swagger documentation
    register_swagger(app)

    # Register audit log model
    try:
        from .services.security_service import create_audit_log_model
        AuditLog = create_audit_log_model()
        app.logger.info("Audit logging enabled")
    except Exception as e:
        app.logger.warning(f"Audit logging could not be enabled: {str(e)}")

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

    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")

    return app


def register_error_handlers(app):
    """Register error handlers for better error responses"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'message': 'Bad request',
            'error': str(error)
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'message': 'Unauthorized',
            'error': str(error)
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'message': 'Forbidden',
            'error': str(error)
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'message': 'Resource not found',
            'error': str(error)
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'message': 'Method not allowed',
            'error': str(error)
        }), 405

    @app.errorhandler(429)
    def too_many_requests(error):
        return jsonify({
            'message': 'Too many requests',
            'error': str(error)
        }), 429

    @app.errorhandler(500)
    def server_error(error):
        app.logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({
            'message': 'Internal server error',
            'error': str(error) if app.config.get('DEBUG', False) else 'See logs for details'
        }), 500
